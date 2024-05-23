/*###########################################################################
 #
 # Copyright (c) 2003 Zope Foundation and Contributors.
 # All Rights Reserved.
 #
 # This software is subject to the provisions of the Zope Public License,
 # Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
 # THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
 # WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 # WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
 # FOR A PARTICULAR PURPOSE.
 #
 ############################################################################*/

#include "Python.h"
#include "structmember.h"

#ifdef __clang__
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wunused-parameter"
#pragma clang diagnostic ignored "-Wmissing-field-initializers"
#endif

#define TYPE(O) ((PyTypeObject*)(O))
#define OBJECT(O) ((PyObject*)(O))
#define CLASSIC(O) ((PyClassObject*)(O))
#ifndef PyVarObject_HEAD_INIT
#define PyVarObject_HEAD_INIT(a, b) PyObject_HEAD_INIT(a) b,
#endif
#ifndef Py_TYPE
#define Py_TYPE(o) ((o)->ob_type)
#endif

#define PyNative_FromString PyUnicode_FromString

/* Public module-scope functions, forward declared here FBO type methods. */
static PyObject *implementedBy(PyObject* module, PyObject *cls);
static PyObject *getObjectSpecification(PyObject *module, PyObject *ob);
static PyObject *providedBy(PyObject *module, PyObject *ob);

/* Static strings, used to invoke PyObject_CallMethodObjArgs */
static PyObject *str_call_conform;
static PyObject *str_uncached_lookup;
static PyObject *str_uncached_lookupAll;
static PyObject *str_uncached_subscriptions;
static PyObject *strchanged;
static PyObject *str__adapt__;

/* Static strings, used to invoke PyObject_GetItem
 *
 * We cannot use PyDict_GetItemString, because the '__dict__' we get
 * from our types can be a 'types.mappingproxy', which causes a segfault.
 */
static PyObject* str__implemented__;
/*
 * Utility: fetch the module for the current type, using the module spec.
 */
static PyObject* _get_module(PyTypeObject *typeobj);   /* forward */

/* Moving these statics to module state. */
static PyObject* adapter_hooks;

static PyTypeObject SpecificationBaseType; /* Forward */

typedef struct
{
    PyObject_HEAD
    PyObject* weakreflist;
    /*
      In the past, these fields were stored in the __dict__
      and were technically allowed to contain any Python object, though
      other type checks would fail or fall back to generic code paths if
      they didn't have the expected type. We preserve that behaviour and don't
      make any assumptions about contents.
    */
    PyObject* _implied;
    /*
      The remainder aren't used in C code but must be stored here
      to prevent instance layout conflicts.
    */
    PyObject* _dependents;
    PyObject* _bases;
    PyObject* _v_attrs;
    PyObject* __iro__;
    PyObject* __sro__;
} Spec;

/*
  We know what the fields are *supposed* to define, but
  they could have anything, so we need to traverse them.
*/
static int
Spec_traverse(Spec* self, visitproc visit, void* arg)
{
    Py_VISIT(self->_implied);
    Py_VISIT(self->_dependents);
    Py_VISIT(self->_bases);
    Py_VISIT(self->_v_attrs);
    Py_VISIT(self->__iro__);
    Py_VISIT(self->__sro__);
    return 0;
}

static int
Spec_clear(Spec* self)
{
    Py_CLEAR(self->_implied);
    Py_CLEAR(self->_dependents);
    Py_CLEAR(self->_bases);
    Py_CLEAR(self->_v_attrs);
    Py_CLEAR(self->__iro__);
    Py_CLEAR(self->__sro__);
    return 0;
}

static void
Spec_dealloc(Spec* self)
{
    /* PyType_GenericAlloc that you get when you don't
       specify a tp_alloc always tracks the object. */
    PyObject_GC_UnTrack((PyObject*)self);
    if (self->weakreflist != NULL) {
        PyObject_ClearWeakRefs(OBJECT(self));
    }
    Spec_clear(self);
    Py_TYPE(self)->tp_free(OBJECT(self));
}

static char Spec_extends__doc__[] =
  "Test whether a specification is or extends another";

static PyObject*
Spec_extends(Spec* self, PyObject* other)
{
    PyObject* implied;

    implied = self->_implied;
    if (implied == NULL) {
        return NULL;
    }

    if (PyDict_GetItem(implied, other) != NULL)
        Py_RETURN_TRUE;
    Py_RETURN_FALSE;
}

static PyObject*
Spec_call(Spec* self, PyObject* args, PyObject* kw)
{
    PyObject* spec;

    if (!PyArg_ParseTuple(args, "O", &spec))
        return NULL;
    return Spec_extends(self, spec);
}

static char Spec_providedBy__doc__[] =
  "Test whether an interface is implemented by the specification";

static PyObject*
Spec_providedBy(PyObject* self, PyObject* ob)
{
    PyObject *decl;
    PyObject *item;
    PyObject *module;

    module = _get_module(Py_TYPE(self));

    decl = providedBy(module, ob);
    if (decl == NULL)
        return NULL;

    if (PyObject_TypeCheck(decl, &SpecificationBaseType))
        item = Spec_extends((Spec*)decl, self);
    else
        /* decl is probably a security proxy.  We have to go the long way
           around.
        */
        item = PyObject_CallFunctionObjArgs(decl, self, NULL);

    Py_DECREF(decl);
    return item;
}

static char Spec_implementedBy__doc__[] =
  "Test whether the specification is implemented by a class or factory.\n"
  "Raise TypeError if argument is neither a class nor a callable.";

static PyObject*
Spec_implementedBy(PyObject* self, PyObject* cls)
{
    PyObject *decl;
    PyObject *item;
    PyObject *module;

    module = _get_module(Py_TYPE(self));

    decl = implementedBy(module, cls);
    if (decl == NULL)
        return NULL;

    if (PyObject_TypeCheck(decl, &SpecificationBaseType))
        item = Spec_extends((Spec*)decl, self);
    else
        item = PyObject_CallFunctionObjArgs(decl, self, NULL);

    Py_DECREF(decl);
    return item;
}

static struct PyMethodDef Spec_methods[] = {
    { "providedBy",
      (PyCFunction)Spec_providedBy,
      METH_O,
      Spec_providedBy__doc__ },
    { "implementedBy",
      (PyCFunction)Spec_implementedBy,
      METH_O,
      Spec_implementedBy__doc__ },
    { "isOrExtends", (PyCFunction)Spec_extends, METH_O, Spec_extends__doc__ },

    { NULL, NULL } /* sentinel */
};

static PyMemberDef Spec_members[] = {
    { "_implied", T_OBJECT_EX, offsetof(Spec, _implied), 0, "" },
    { "_dependents", T_OBJECT_EX, offsetof(Spec, _dependents), 0, "" },
    { "_bases", T_OBJECT_EX, offsetof(Spec, _bases), 0, "" },
    { "_v_attrs", T_OBJECT_EX, offsetof(Spec, _v_attrs), 0, "" },
    { "__iro__", T_OBJECT_EX, offsetof(Spec, __iro__), 0, "" },
    { "__sro__", T_OBJECT_EX, offsetof(Spec, __sro__), 0, "" },
    { NULL },
};

static char Spec__doc__[] = "Base type for Specification objects";

static PyTypeObject SpecificationBaseType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name="_interface_coptimizations.SpecificationBase",
    .tp_doc=Spec__doc__,
    .tp_basicsize=sizeof(Spec),
    .tp_flags=Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_weaklistoffset=offsetof(Spec, weakreflist),
    .tp_methods=Spec_methods,
    .tp_members=Spec_members,
    .tp_call=(ternaryfunc)Spec_call,
    .tp_traverse=(traverseproc)Spec_traverse,
    .tp_clear=(inquiry)Spec_clear,
    .tp_dealloc=(destructor)Spec_dealloc,
};

static PyObject*
OSD_descr_get(PyObject* self, PyObject* inst, PyObject* cls)
{
    PyObject* provides;
    PyObject *module;

    module = _get_module(Py_TYPE(self));

    if (inst == NULL)
        return getObjectSpecification(module, cls);

    provides = PyObject_GetAttrString(inst, "__provides__");
    /* Return __provides__ if we got it, or return NULL and propagate
     * non-AttributeError. */
    if (provides != NULL || !PyErr_ExceptionMatches(PyExc_AttributeError))
        return provides;

    PyErr_Clear();

    return implementedBy(module, cls);
}

static char OSD__doc__[] = "Object Specification Descriptor";

static PyTypeObject OSDType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name="_interface_coptimizations.ObjectSpecificationDescriptor",
    .tp_doc=OSD__doc__,
    .tp_flags=Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_descr_get=(descrgetfunc)OSD_descr_get,
};

typedef struct
{
    Spec spec;
    /* These members are handled generically, as for Spec members. */
    PyObject* _cls;
    PyObject* _implements;
} CPB;

static PyObject*
CPB_descr_get(CPB* self, PyObject* inst, PyObject* cls)
{
    PyObject* implements;

    if (self->_cls == NULL)
        return NULL;

    if (cls == self->_cls) {
        if (inst == NULL) {
            Py_INCREF(self);
            return OBJECT(self);
        }

        implements = self->_implements;
        Py_XINCREF(implements);
        return implements;
    }

    PyErr_SetString(PyExc_AttributeError, "__provides__");
    return NULL;
}

static int
CPB_traverse(CPB* self, visitproc visit, void* arg)
{
    Py_VISIT(self->_cls);
    Py_VISIT(self->_implements);
    return Spec_traverse((Spec*)self, visit, arg);
}

static int
CPB_clear(CPB* self)
{
    Py_CLEAR(self->_cls);
    Py_CLEAR(self->_implements);
    Spec_clear((Spec*)self);
    return 0;
}

static void
CPB_dealloc(CPB* self)
{
    PyObject_GC_UnTrack((PyObject*)self);
    CPB_clear(self);
    Spec_dealloc((Spec*)self);
}

static PyMemberDef CPB_members[] = {
    { "_cls", T_OBJECT_EX, offsetof(CPB, _cls), 0, "Defining class." },
    { "_implements",
      T_OBJECT_EX,
      offsetof(CPB, _implements),
      0,
      "Result of implementedBy." },
    { NULL }
};

static char CPB__doc__[] = "C Base class for ClassProvides";

static PyTypeObject CPBType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name="_interface_coptimizations.ClassProvidesBase",
    .tp_doc=CPB__doc__,
    .tp_basicsize=sizeof(CPB),
    .tp_flags=Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_base=&SpecificationBaseType,
    .tp_members=CPB_members,
    .tp_descr_get=(descrgetfunc)CPB_descr_get,
    .tp_clear=(inquiry)CPB_clear,
    .tp_traverse=(traverseproc)CPB_traverse,
    .tp_dealloc=(destructor)CPB_dealloc,
};

/* ==================================================================== */
/* ========== Begin: __call__ and __adapt__ =========================== */

/*
    def __adapt__(self, obj):
        """Adapt an object to the receiver
        """
        if self.providedBy(obj):
            return obj

        for hook in adapter_hooks:
            adapter = hook(self, obj)
            if adapter is not None:
                return adapter


*/
static PyObject*
__adapt__(PyObject* self, PyObject* obj)
{
    PyObject *decl;
    PyObject *args;
    PyObject *adapter;
    PyObject *module;
    int implements;
    int i;
    int l;

    module = _get_module(Py_TYPE(self));

    decl = providedBy(module, obj);
    if (decl == NULL)
        return NULL;

    if (PyObject_TypeCheck(decl, &SpecificationBaseType)) {
        PyObject* implied;

        implied = ((Spec*)decl)->_implied;
        if (implied == NULL) {
            Py_DECREF(decl);
            return NULL;
        }

        implements = PyDict_GetItem(implied, self) != NULL;
        Py_DECREF(decl);
    } else {
        /* decl is probably a security proxy.  We have to go the long way
           around.
        */
        PyObject* r;
        r = PyObject_CallFunctionObjArgs(decl, self, NULL);
        Py_DECREF(decl);
        if (r == NULL)
            return NULL;
        implements = PyObject_IsTrue(r);
        Py_DECREF(r);
    }

    if (implements) {
        Py_INCREF(obj);
        return obj;
    }

    l = PyList_GET_SIZE(adapter_hooks);
    args = PyTuple_New(2);
    if (args == NULL)
        return NULL;
    Py_INCREF(self);
    PyTuple_SET_ITEM(args, 0, self);
    Py_INCREF(obj);
    PyTuple_SET_ITEM(args, 1, obj);
    for (i = 0; i < l; i++) {
        adapter = PyObject_CallObject(PyList_GET_ITEM(adapter_hooks, i), args);
        if (adapter == NULL || adapter != Py_None) {
            Py_DECREF(args);
            return adapter;
        }
        Py_DECREF(adapter);
    }

    Py_DECREF(args);

    Py_INCREF(Py_None);
    return Py_None;
}

typedef struct
{
    Spec spec;
    PyObject* __name__;
    PyObject* __module__;
    Py_hash_t _v_cached_hash;
} IB;

static struct PyMethodDef ib_methods[] = {
    { "__adapt__",
      (PyCFunction)__adapt__,
      METH_O,
      "Adapt an object to the receiver" },
    { NULL, NULL } /* sentinel */
};

/*
    def __call__(self, obj, alternate=_marker):
        try:
            conform = obj.__conform__
        except AttributeError: # pylint:disable=bare-except
            conform = None

        if conform is not None:
            adapter = self._call_conform(conform)
            if adapter is not None:
                return adapter

        adapter = self.__adapt__(obj)

        if adapter is not None:
            return adapter
        if alternate is not _marker:
            return alternate
        raise TypeError("Could not adapt", obj, self)

*/
static PyObject*
IB_call(PyObject* self, PyObject* args, PyObject* kwargs)
{
    PyObject *conform, *obj, *alternate, *adapter;
    static char* kwlist[] = { "obj", "alternate", NULL };
    conform = obj = alternate = adapter = NULL;

    if (!PyArg_ParseTupleAndKeywords(
          args, kwargs, "O|O", kwlist, &obj, &alternate))
        return NULL;

    conform = PyObject_GetAttrString(obj, "__conform__");
    if (conform == NULL) {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
            /* Propagate non-AttributeErrors */
            return NULL;
        }
        PyErr_Clear();

        Py_INCREF(Py_None);
        conform = Py_None;
    }

    if (conform != Py_None) {
        adapter =
          PyObject_CallMethodObjArgs(self, str_call_conform, conform, NULL);
        Py_DECREF(conform);
        if (adapter == NULL || adapter != Py_None)
            return adapter;
        Py_DECREF(adapter);
    } else {
        Py_DECREF(conform);
    }

    /* We differ from the Python code here. For speed, instead of always calling
       self.__adapt__(), we check to see if the type has defined it. Checking in
       the dict for __adapt__ isn't sufficient because there's no cheap way to
       tell if it's the __adapt__ that InterfaceBase itself defines (our type
       will *never* be InterfaceBase, we're always subclassed by
       InterfaceClass). Instead, we cooperate with InterfaceClass in Python to
       set a flag in a new subclass when this is necessary. */
    if (PyDict_GetItemString(self->ob_type->tp_dict, "_CALL_CUSTOM_ADAPT")) {
        /* Doesn't matter what the value is. Simply being present is enough. */
        adapter = PyObject_CallMethodObjArgs(self, str__adapt__, obj, NULL);
    } else {
        adapter = __adapt__(self, obj);
    }

    if (adapter == NULL || adapter != Py_None) {
        return adapter;
    }
    Py_DECREF(adapter);

    if (alternate != NULL) {
        Py_INCREF(alternate);
        return alternate;
    }

    adapter = Py_BuildValue("sOO", "Could not adapt", obj, self);
    if (adapter != NULL) {
        PyErr_SetObject(PyExc_TypeError, adapter);
        Py_DECREF(adapter);
    }
    return NULL;
}

static int
IB_traverse(IB* self, visitproc visit, void* arg)
{
    Py_VISIT(self->__name__);
    Py_VISIT(self->__module__);
    return Spec_traverse((Spec*)self, visit, arg);
}

static int
IB_clear(IB* self)
{
    Py_CLEAR(self->__name__);
    Py_CLEAR(self->__module__);
    return Spec_clear((Spec*)self);
}

static void
IB_dealloc(IB* self)
{
    PyObject_GC_UnTrack((PyObject*)self);
    IB_clear(self);
    Spec_dealloc((Spec*)self);
}

static PyMemberDef IB_members[] = {
    { "__name__", T_OBJECT_EX, offsetof(IB, __name__), 0, "" },
    // The redundancy between __module__ and __ibmodule__ is because
    // __module__ is often shadowed by subclasses.
    { "__module__", T_OBJECT_EX, offsetof(IB, __module__), READONLY, "" },
    { "__ibmodule__", T_OBJECT_EX, offsetof(IB, __module__), 0, "" },
    { NULL }
};

static Py_hash_t
IB_hash(IB* self)
{
    PyObject* tuple;
    if (!self->__module__) {
        PyErr_SetString(PyExc_AttributeError, "__module__");
        return -1;
    }
    if (!self->__name__) {
        PyErr_SetString(PyExc_AttributeError, "__name__");
        return -1;
    }

    if (self->_v_cached_hash) {
        return self->_v_cached_hash;
    }

    tuple = PyTuple_Pack(2, self->__name__, self->__module__);
    if (!tuple) {
        return -1;
    }
    self->_v_cached_hash = PyObject_Hash(tuple);
    Py_CLEAR(tuple);
    return self->_v_cached_hash;
}

static PyTypeObject InterfaceBaseType;

static PyObject*
IB_richcompare(IB* self, PyObject* other, int op)
{
    PyObject* othername;
    PyObject* othermod;
    PyObject* oresult;
    IB* otherib;
    int result;

    otherib = NULL;
    oresult = othername = othermod = NULL;

    if (OBJECT(self) == other) {
        switch (op) {
            case Py_EQ:
            case Py_LE:
            case Py_GE:
                Py_RETURN_TRUE;
                break;
            case Py_NE:
                Py_RETURN_FALSE;
        }
    }

    if (other == Py_None) {
        switch (op) {
            case Py_LT:
            case Py_LE:
            case Py_NE:
                Py_RETURN_TRUE;
            default:
                Py_RETURN_FALSE;
        }
    }

    if (PyObject_TypeCheck(other, &InterfaceBaseType)) {
        // This branch borrows references. No need to clean
        // up if otherib is not null.
        otherib = (IB*)other;
        othername = otherib->__name__;
        othermod = otherib->__module__;
    } else {
        othername = PyObject_GetAttrString(other, "__name__");
        if (othername) {
            othermod = PyObject_GetAttrString(other, "__module__");
        }
        if (!othername || !othermod) {
            if (PyErr_Occurred() &&
                PyErr_ExceptionMatches(PyExc_AttributeError)) {
                PyErr_Clear();
                oresult = Py_NotImplemented;
            }
            goto cleanup;
        }
    }
#if 0
// This is the simple, straightforward version of what Python does.
    PyObject* pt1 = PyTuple_Pack(2, self->__name__, self->__module__);
    PyObject* pt2 = PyTuple_Pack(2, othername, othermod);
    oresult = PyObject_RichCompare(pt1, pt2, op);
#endif

    // tuple comparison is decided by the first non-equal element.
    result = PyObject_RichCompareBool(self->__name__, othername, Py_EQ);
    if (result == 0) {
        result = PyObject_RichCompareBool(self->__name__, othername, op);
    } else if (result == 1) {
        result = PyObject_RichCompareBool(self->__module__, othermod, op);
    }
    // If either comparison failed, we have an error set.
    // Leave oresult NULL so we raise it.
    if (result == -1) {
        goto cleanup;
    }

    oresult = result ? Py_True : Py_False;

cleanup:
    Py_XINCREF(oresult);

    if (!otherib) {
        Py_XDECREF(othername);
        Py_XDECREF(othermod);
    }
    return oresult;
}

static int
IB_init(IB* self, PyObject* args, PyObject* kwargs)
{
    static char* kwlist[] = { "__name__", "__module__", NULL };
    PyObject* module = NULL;
    PyObject* name = NULL;

    if (!PyArg_ParseTupleAndKeywords(
          args, kwargs, "|OO:InterfaceBase.__init__", kwlist, &name, &module)) {
        return -1;
    }
    IB_clear(self);
    self->__module__ = module ? module : Py_None;
    Py_INCREF(self->__module__);
    self->__name__ = name ? name : Py_None;
    Py_INCREF(self->__name__);
    return 0;
}

static char IB__doc__[] = (
    "Interface base type providing __call__ and __adapt__"
);

static PyTypeObject InterfaceBaseType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name="_zope_interface_coptimizations.InterfaceBase",
    .tp_doc=IB__doc__,
    .tp_basicsize=sizeof(IB),
    .tp_flags=Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_base=&SpecificationBaseType,
    .tp_methods=ib_methods,
    .tp_members=IB_members,
    .tp_init=(initproc)IB_init,
    .tp_richcompare=(richcmpfunc)IB_richcompare,
    .tp_hash=(hashfunc)IB_hash,
    .tp_call=(ternaryfunc)IB_call,
    .tp_traverse=(traverseproc)IB_traverse,
    .tp_clear=(inquiry)IB_clear,
    .tp_dealloc=(destructor)IB_dealloc,
};

/* =================== End: __call__ and __adapt__ ==================== */
/* ==================================================================== */

/* ==================================================================== */
/* ========================== Begin: Lookup Bases ===================== */

typedef struct
{
    PyObject_HEAD
    PyObject* _cache;
    PyObject* _mcache;
    PyObject* _scache;
} lookup;

typedef struct
{
    PyObject_HEAD
    PyObject* _cache;
    PyObject* _mcache;
    PyObject* _scache;
    PyObject* _verify_ro;
    PyObject* _verify_generations;
} verify;

static int
lookup_traverse(lookup* self, visitproc visit, void* arg)
{
    int vret;

    if (self->_cache) {
        vret = visit(self->_cache, arg);
        if (vret != 0)
            return vret;
    }

    if (self->_mcache) {
        vret = visit(self->_mcache, arg);
        if (vret != 0)
            return vret;
    }

    if (self->_scache) {
        vret = visit(self->_scache, arg);
        if (vret != 0)
            return vret;
    }

    return 0;
}

static int
lookup_clear(lookup* self)
{
    Py_CLEAR(self->_cache);
    Py_CLEAR(self->_mcache);
    Py_CLEAR(self->_scache);
    return 0;
}

static void
lookup_dealloc(lookup* self)
{
    PyObject_GC_UnTrack((PyObject*)self);
    lookup_clear(self);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

/*
    def changed(self, ignored=None):
        self._cache.clear()
        self._mcache.clear()
        self._scache.clear()
*/
static PyObject*
lookup_changed(lookup* self, PyObject* ignored)
{
    lookup_clear(self);
    Py_INCREF(Py_None);
    return Py_None;
}

#define ASSURE_DICT(N)                                                         \
    if (N == NULL) {                                                           \
        N = PyDict_New();                                                      \
        if (N == NULL)                                                         \
            return NULL;                                                       \
    }

/*
    def _getcache(self, provided, name):
        cache = self._cache.get(provided)
        if cache is None:
            cache = {}
            self._cache[provided] = cache
        if name:
            c = cache.get(name)
            if c is None:
                c = {}
                cache[name] = c
            cache = c
        return cache
*/
static PyObject*
_subcache(PyObject* cache, PyObject* key)
{
    PyObject* subcache;

    subcache = PyDict_GetItem(cache, key);
    if (subcache == NULL) {
        int status;

        subcache = PyDict_New();
        if (subcache == NULL)
            return NULL;
        status = PyDict_SetItem(cache, key, subcache);
        Py_DECREF(subcache);
        if (status < 0)
            return NULL;
    }

    return subcache;
}
static PyObject*
_getcache(lookup* self, PyObject* provided, PyObject* name)
{
    PyObject* cache;

    ASSURE_DICT(self->_cache);
    cache = _subcache(self->_cache, provided);
    if (cache == NULL)
        return NULL;

    if (name != NULL && PyObject_IsTrue(name))
        cache = _subcache(cache, name);

    return cache;
}

/*
    def lookup(self, required, provided, name=u'', default=None):
        cache = self._getcache(provided, name)
        if len(required) == 1:
            result = cache.get(required[0], _not_in_mapping)
        else:
            result = cache.get(tuple(required), _not_in_mapping)

        if result is _not_in_mapping:
            result = self._uncached_lookup(required, provided, name)
            if len(required) == 1:
                cache[required[0]] = result
            else:
                cache[tuple(required)] = result

        if result is None:
            return default

        return result
*/

static PyObject*
_lookup(lookup* self,
        PyObject* required,
        PyObject* provided,
        PyObject* name,
        PyObject* default_)
{
    PyObject *result, *key, *cache;
    result = key = cache = NULL;
    if (name && !PyUnicode_Check(name)) {
        PyErr_SetString(PyExc_ValueError, "name is not a string or unicode");
        return NULL;
    }

    /* If `required` is a lazy sequence, it could have arbitrary side-effects,
       such as clearing our caches. So we must not retrieve the cache until
       after resolving it. */
    required = PySequence_Tuple(required);
    if (required == NULL)
        return NULL;

    cache = _getcache(self, provided, name);
    if (cache == NULL)
        return NULL;

    if (PyTuple_GET_SIZE(required) == 1)
        key = PyTuple_GET_ITEM(required, 0);
    else
        key = required;

    result = PyDict_GetItem(cache, key);
    if (result == NULL) {
        int status;

        result = PyObject_CallMethodObjArgs(
          OBJECT(self), str_uncached_lookup, required, provided, name, NULL);
        if (result == NULL) {
            Py_DECREF(required);
            return NULL;
        }
        status = PyDict_SetItem(cache, key, result);
        Py_DECREF(required);
        if (status < 0) {
            Py_DECREF(result);
            return NULL;
        }
    } else {
        Py_INCREF(result);
        Py_DECREF(required);
    }

    if (result == Py_None && default_ != NULL) {
        Py_DECREF(Py_None);
        Py_INCREF(default_);
        return default_;
    }

    return result;
}
static PyObject*
lookup_lookup(lookup* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "required", "provided", "name", "default", NULL };
    PyObject *required, *provided, *name = NULL, *default_ = NULL;

    if (!PyArg_ParseTupleAndKeywords(args,
                                     kwds,
                                     "OO|OO:LookupBase.lookup",
                                     kwlist,
                                     &required,
                                     &provided,
                                     &name,
                                     &default_))
        return NULL;

    return _lookup(self, required, provided, name, default_);
}

/*
    def lookup1(self, required, provided, name=u'', default=None):
        cache = self._getcache(provided, name)
        result = cache.get(required, _not_in_mapping)
        if result is _not_in_mapping:
            return self.lookup((required, ), provided, name, default)

        if result is None:
            return default

        return result
*/
static PyObject*
_lookup1(lookup* self,
         PyObject* required,
         PyObject* provided,
         PyObject* name,
         PyObject* default_)
{
    PyObject *result, *cache;

    if (name && !PyUnicode_Check(name)) {
        PyErr_SetString(PyExc_ValueError, "name is not a string or unicode");
        return NULL;
    }

    cache = _getcache(self, provided, name);
    if (cache == NULL)
        return NULL;

    result = PyDict_GetItem(cache, required);
    if (result == NULL) {
        PyObject* tup;

        tup = PyTuple_New(1);
        if (tup == NULL)
            return NULL;
        Py_INCREF(required);
        PyTuple_SET_ITEM(tup, 0, required);
        result = _lookup(self, tup, provided, name, default_);
        Py_DECREF(tup);
    } else {
        if (result == Py_None && default_ != NULL) {
            result = default_;
        }
        Py_INCREF(result);
    }

    return result;
}
static PyObject*
lookup_lookup1(lookup* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "required", "provided", "name", "default", NULL };
    PyObject *required, *provided, *name = NULL, *default_ = NULL;

    if (!PyArg_ParseTupleAndKeywords(args,
                                     kwds,
                                     "OO|OO:LookupBase.lookup1",
                                     kwlist,
                                     &required,
                                     &provided,
                                     &name,
                                     &default_))
        return NULL;

    return _lookup1(self, required, provided, name, default_);
}

/*
    def adapter_hook(self, provided, object, name=u'', default=None):
        required = providedBy(object)
        cache = self._getcache(provided, name)
        factory = cache.get(required, _not_in_mapping)
        if factory is _not_in_mapping:
            factory = self.lookup((required, ), provided, name)

        if factory is not None:
            if isinstance(object, super):
                object = object.__self__
            result = factory(object)
            if result is not None:
                return result

        return default
*/
static PyObject*
_adapter_hook(lookup* self,
              PyObject* provided,
              PyObject* object,
              PyObject* name,
              PyObject* default_)
{
    PyObject *required;
    PyObject *factory;
    PyObject *result;
    PyObject *module;

    module = _get_module(Py_TYPE(self));

    if (name && !PyUnicode_Check(name)) {
        PyErr_SetString(PyExc_ValueError, "name is not a string or unicode");
        return NULL;
    }

    required = providedBy(module, object);
    if (required == NULL)
        return NULL;

    factory = _lookup1(self, required, provided, name, Py_None);
    Py_DECREF(required);
    if (factory == NULL)
        return NULL;

    if (factory != Py_None) {
        if (PyObject_TypeCheck(object, &PySuper_Type)) {
            PyObject* self = PyObject_GetAttrString(object, "__self__");
            if (self == NULL) {
                Py_DECREF(factory);
                return NULL;
            }
            // Borrow the reference to self
            Py_DECREF(self);
            object = self;
        }
        result = PyObject_CallFunctionObjArgs(factory, object, NULL);
        Py_DECREF(factory);
        if (result == NULL || result != Py_None)
            return result;
    } else
        result = factory; /* None */

    if (default_ == NULL || default_ == result) /* No default specified, */
        return result; /* Return None.  result is owned None */

    Py_DECREF(result);
    Py_INCREF(default_);

    return default_;
}
static PyObject*
lookup_adapter_hook(lookup* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "provided", "object", "name", "default", NULL };
    PyObject *object, *provided, *name = NULL, *default_ = NULL;

    if (!PyArg_ParseTupleAndKeywords(args,
                                     kwds,
                                     "OO|OO:LookupBase.adapter_hook",
                                     kwlist,
                                     &provided,
                                     &object,
                                     &name,
                                     &default_))
        return NULL;

    return _adapter_hook(self, provided, object, name, default_);
}

static PyObject*
lookup_queryAdapter(lookup* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "object", "provided", "name", "default", NULL };
    PyObject *object, *provided, *name = NULL, *default_ = NULL;

    if (!PyArg_ParseTupleAndKeywords(args,
                                     kwds,
                                     "OO|OO:LookupBase.queryAdapter",
                                     kwlist,
                                     &object,
                                     &provided,
                                     &name,
                                     &default_))
        return NULL;

    return _adapter_hook(self, provided, object, name, default_);
}

/*
    def lookupAll(self, required, provided):
        cache = self._mcache.get(provided)
        if cache is None:
            cache = {}
            self._mcache[provided] = cache

        required = tuple(required)
        result = cache.get(required, _not_in_mapping)
        if result is _not_in_mapping:
            result = self._uncached_lookupAll(required, provided)
            cache[required] = result

        return result
*/
static PyObject*
_lookupAll(lookup* self, PyObject* required, PyObject* provided)
{
    PyObject *cache, *result;

    /* resolve before getting cache. See note in _lookup. */
    required = PySequence_Tuple(required);
    if (required == NULL)
        return NULL;

    ASSURE_DICT(self->_mcache);
    cache = _subcache(self->_mcache, provided);
    if (cache == NULL)
        return NULL;

    result = PyDict_GetItem(cache, required);
    if (result == NULL) {
        int status;

        result = PyObject_CallMethodObjArgs(
          OBJECT(self), str_uncached_lookupAll, required, provided, NULL);
        if (result == NULL) {
            Py_DECREF(required);
            return NULL;
        }
        status = PyDict_SetItem(cache, required, result);
        Py_DECREF(required);
        if (status < 0) {
            Py_DECREF(result);
            return NULL;
        }
    } else {
        Py_INCREF(result);
        Py_DECREF(required);
    }

    return result;
}
static PyObject*
lookup_lookupAll(lookup* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "required", "provided", NULL };
    PyObject *required, *provided;

    if (!PyArg_ParseTupleAndKeywords(
          args, kwds, "OO:LookupBase.lookupAll", kwlist, &required, &provided))
        return NULL;

    return _lookupAll(self, required, provided);
}

/*
    def subscriptions(self, required, provided):
        cache = self._scache.get(provided)
        if cache is None:
            cache = {}
            self._scache[provided] = cache

        required = tuple(required)
        result = cache.get(required, _not_in_mapping)
        if result is _not_in_mapping:
            result = self._uncached_subscriptions(required, provided)
            cache[required] = result

        return result
*/
static PyObject*
_subscriptions(lookup* self, PyObject* required, PyObject* provided)
{
    PyObject *cache, *result;

    /* resolve before getting cache. See note in _lookup. */
    required = PySequence_Tuple(required);
    if (required == NULL)
        return NULL;

    ASSURE_DICT(self->_scache);
    cache = _subcache(self->_scache, provided);
    if (cache == NULL)
        return NULL;

    result = PyDict_GetItem(cache, required);
    if (result == NULL) {
        int status;

        result = PyObject_CallMethodObjArgs(
          OBJECT(self), str_uncached_subscriptions, required, provided, NULL);
        if (result == NULL) {
            Py_DECREF(required);
            return NULL;
        }
        status = PyDict_SetItem(cache, required, result);
        Py_DECREF(required);
        if (status < 0) {
            Py_DECREF(result);
            return NULL;
        }
    } else {
        Py_INCREF(result);
        Py_DECREF(required);
    }

    return result;
}
static PyObject*
lookup_subscriptions(lookup* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "required", "provided", NULL };
    PyObject *required, *provided;

    if (!PyArg_ParseTupleAndKeywords(
          args, kwds, "OO", kwlist, &required, &provided))
        return NULL;

    return _subscriptions(self, required, provided);
}

static struct PyMethodDef lookup_methods[] = {
    { "changed", (PyCFunction)lookup_changed, METH_O, "" },
    { "lookup", (PyCFunction)lookup_lookup, METH_KEYWORDS | METH_VARARGS, "" },
    { "lookup1",
      (PyCFunction)lookup_lookup1,
      METH_KEYWORDS | METH_VARARGS,
      "" },
    { "queryAdapter",
      (PyCFunction)lookup_queryAdapter,
      METH_KEYWORDS | METH_VARARGS,
      "" },
    { "adapter_hook",
      (PyCFunction)lookup_adapter_hook,
      METH_KEYWORDS | METH_VARARGS,
      "" },
    { "lookupAll",
      (PyCFunction)lookup_lookupAll,
      METH_KEYWORDS | METH_VARARGS,
      "" },
    { "subscriptions",
      (PyCFunction)lookup_subscriptions,
      METH_KEYWORDS | METH_VARARGS,
      "" },
    { NULL, NULL } /* sentinel */
};

static char LookupBase__doc__[] = "Base class for adapter registries";

static PyTypeObject LookupBase = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name="_zope_interface_coptimizations.LookupBase",
    .tp_doc=LookupBase__doc__,
    .tp_basicsize=sizeof(lookup),
    .tp_flags=Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_methods=lookup_methods,
    .tp_traverse=(traverseproc)lookup_traverse,
    .tp_clear=(inquiry)lookup_clear,
    .tp_dealloc=(destructor)&lookup_dealloc,
};

static int
verifying_traverse(verify* self, visitproc visit, void* arg)
{
    int vret;

    vret = lookup_traverse((lookup*)self, visit, arg);
    if (vret != 0)
        return vret;

    if (self->_verify_ro) {
        vret = visit(self->_verify_ro, arg);
        if (vret != 0)
            return vret;
    }
    if (self->_verify_generations) {
        vret = visit(self->_verify_generations, arg);
        if (vret != 0)
            return vret;
    }

    return 0;
}

static int
verifying_clear(verify* self)
{
    lookup_clear((lookup*)self);
    Py_CLEAR(self->_verify_generations);
    Py_CLEAR(self->_verify_ro);
    return 0;
}

static void
verifying_dealloc(verify* self)
{
    PyObject_GC_UnTrack((PyObject*)self);
    verifying_clear(self);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

/*
    def changed(self, originally_changed):
        super(VerifyingBasePy, self).changed(originally_changed)
        self._verify_ro = self._registry.ro[1:]
        self._verify_generations = [r._generation for r in self._verify_ro]
*/
static PyObject*
_generations_tuple(PyObject* ro)
{
    int i, l;
    PyObject* generations;

    l = PyTuple_GET_SIZE(ro);
    generations = PyTuple_New(l);
    for (i = 0; i < l; i++) {
        PyObject* generation;

        generation = PyObject_GetAttrString(
            PyTuple_GET_ITEM(ro, i), "_generation");
        if (generation == NULL) {
            Py_DECREF(generations);
            return NULL;
        }
        PyTuple_SET_ITEM(generations, i, generation);
    }

    return generations;
}
static PyObject*
verifying_changed(verify* self, PyObject* ignored)
{
    PyObject *t, *ro;

    verifying_clear(self);

    t = PyObject_GetAttrString(OBJECT(self), "_registry");
    if (t == NULL)
        return NULL;
    ro = PyObject_GetAttrString(t, "ro");
    Py_DECREF(t);
    if (ro == NULL)
        return NULL;

    t = PyObject_CallFunctionObjArgs(OBJECT(&PyTuple_Type), ro, NULL);
    Py_DECREF(ro);
    if (t == NULL)
        return NULL;

    ro = PyTuple_GetSlice(t, 1, PyTuple_GET_SIZE(t));
    Py_DECREF(t);
    if (ro == NULL)
        return NULL;

    self->_verify_generations = _generations_tuple(ro);
    if (self->_verify_generations == NULL) {
        Py_DECREF(ro);
        return NULL;
    }

    self->_verify_ro = ro;

    Py_INCREF(Py_None);
    return Py_None;
}

/*
    def _verify(self):
        if ([r._generation for r in self._verify_ro]
            != self._verify_generations):
            self.changed(None)
*/
static int
_verify(verify* self)
{
    PyObject* changed_result;

    if (self->_verify_ro != NULL && self->_verify_generations != NULL) {
        PyObject* generations;
        int changed;

        generations = _generations_tuple(self->_verify_ro);
        if (generations == NULL)
            return -1;

        changed = PyObject_RichCompareBool(
          self->_verify_generations, generations, Py_NE);
        Py_DECREF(generations);
        if (changed == -1)
            return -1;

        if (changed == 0)
            return 0;
    }

    changed_result =
      PyObject_CallMethodObjArgs(OBJECT(self), strchanged, Py_None, NULL);
    if (changed_result == NULL)
        return -1;

    Py_DECREF(changed_result);
    return 0;
}

static PyObject*
verifying_lookup(verify* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "required", "provided", "name", "default", NULL };
    PyObject *required, *provided, *name = NULL, *default_ = NULL;

    if (!PyArg_ParseTupleAndKeywords(
          args, kwds, "OO|OO", kwlist, &required, &provided, &name, &default_))
        return NULL;

    if (_verify(self) < 0)
        return NULL;

    return _lookup((lookup*)self, required, provided, name, default_);
}

static PyObject*
verifying_lookup1(verify* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "required", "provided", "name", "default", NULL };
    PyObject *required, *provided, *name = NULL, *default_ = NULL;

    if (!PyArg_ParseTupleAndKeywords(
          args, kwds, "OO|OO", kwlist, &required, &provided, &name, &default_))
        return NULL;

    if (_verify(self) < 0)
        return NULL;

    return _lookup1((lookup*)self, required, provided, name, default_);
}

static PyObject*
verifying_adapter_hook(verify* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "provided", "object", "name", "default", NULL };
    PyObject *object, *provided, *name = NULL, *default_ = NULL;

    if (!PyArg_ParseTupleAndKeywords(
          args, kwds, "OO|OO", kwlist, &provided, &object, &name, &default_))
        return NULL;

    if (_verify(self) < 0)
        return NULL;

    return _adapter_hook((lookup*)self, provided, object, name, default_);
}

static PyObject*
verifying_queryAdapter(verify* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "object", "provided", "name", "default", NULL };
    PyObject *object, *provided, *name = NULL, *default_ = NULL;

    if (!PyArg_ParseTupleAndKeywords(
          args, kwds, "OO|OO", kwlist, &object, &provided, &name, &default_))
        return NULL;

    if (_verify(self) < 0)
        return NULL;

    return _adapter_hook((lookup*)self, provided, object, name, default_);
}

static PyObject*
verifying_lookupAll(verify* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "required", "provided", NULL };
    PyObject *required, *provided;

    if (!PyArg_ParseTupleAndKeywords(
          args, kwds, "OO", kwlist, &required, &provided))
        return NULL;

    if (_verify(self) < 0)
        return NULL;

    return _lookupAll((lookup*)self, required, provided);
}

static PyObject*
verifying_subscriptions(verify* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "required", "provided", NULL };
    PyObject *required, *provided;

    if (!PyArg_ParseTupleAndKeywords(
          args, kwds, "OO", kwlist, &required, &provided))
        return NULL;

    if (_verify(self) < 0)
        return NULL;

    return _subscriptions((lookup*)self, required, provided);
}

static struct PyMethodDef verifying_methods[] = {
    { "changed", (PyCFunction)verifying_changed, METH_O, "" },
    { "lookup",
      (PyCFunction)verifying_lookup,
      METH_KEYWORDS | METH_VARARGS,
      "" },
    { "lookup1",
      (PyCFunction)verifying_lookup1,
      METH_KEYWORDS | METH_VARARGS,
      "" },
    { "queryAdapter",
      (PyCFunction)verifying_queryAdapter,
      METH_KEYWORDS | METH_VARARGS,
      "" },
    { "adapter_hook",
      (PyCFunction)verifying_adapter_hook,
      METH_KEYWORDS | METH_VARARGS,
      "" },
    { "lookupAll",
      (PyCFunction)verifying_lookupAll,
      METH_KEYWORDS | METH_VARARGS,
      "" },
    { "subscriptions",
      (PyCFunction)verifying_subscriptions,
      METH_KEYWORDS | METH_VARARGS,
      "" },
    { NULL, NULL } /* sentinel */
};

static char VerifyingBase__doc__[] = (
"Base class for verifying adapter registries."
);

static PyTypeObject VerifyingBase = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name="_zope_interface_coptimizations.VerifyingBase",
    .tp_doc=VerifyingBase__doc__,
    .tp_basicsize=sizeof(verify),
    .tp_flags=Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_base=&LookupBase,
    .tp_methods=verifying_methods,
    .tp_traverse=(traverseproc)verifying_traverse,
    .tp_clear=(inquiry)verifying_clear,
    .tp_dealloc=(destructor)&verifying_dealloc,
};

/*
 * Module state struct:  holds all data formerly kept as static globals.
 */
typedef struct
{
    /* our globals (exposed to Python) */
    PyTypeObject* specification_base_class;
    PyTypeObject* object_specification_descriptor_class;
    PyTypeObject* class_provides_base_class;
    PyTypeObject* interface_base_class;
    PyTypeObject* lookup_base_class;
    PyTypeObject* verifying_base_class;
    PyObject* adapter_hooks;
    /* members importe from 'zope.interface.declarations'
     */
    PyObject* empty;
    PyObject* fallback;
    PyObject* builtin_impl_specs;
    PyTypeObject* implements_class;
    /* flag:  have we importe the next set of members yet from
     * 'zope.interface.declarations?
     */
    int decl_imported;
} _zic_module_state;

/*
 *  Macro to speed lookup of state members
 */
#define _zic_state(o) ((_zic_module_state*)PyModule_GetState(o))

static _zic_module_state*
_zic_state_init(PyObject* module)
{
    _zic_module_state* rec = _zic_state(module);

    rec->specification_base_class = NULL;
    rec->object_specification_descriptor_class = NULL;
    rec->class_provides_base_class = NULL;
    rec->interface_base_class = NULL;
    rec->lookup_base_class = NULL;
    rec->verifying_base_class = NULL;
    rec->adapter_hooks = NULL;

    rec->builtin_impl_specs = NULL;
    rec->empty = NULL;
    rec->fallback = NULL;
    rec->implements_class = NULL;
    rec->decl_imported = 0;

    return rec;
}

static int
_zic_state_traverse(PyObject* module, visitproc visit, void* arg)
{
    _zic_module_state* rec = _zic_state(module);

    Py_VISIT(rec->specification_base_class);
    Py_VISIT(rec->object_specification_descriptor_class);
    Py_VISIT(rec->class_provides_base_class);
    Py_VISIT(rec->interface_base_class);
    Py_VISIT(rec->lookup_base_class);
    Py_VISIT(rec->verifying_base_class);
    Py_VISIT(rec->adapter_hooks);

    Py_VISIT(rec->builtin_impl_specs);
    Py_VISIT(rec->empty);
    Py_VISIT(rec->fallback);
    Py_VISIT(rec->implements_class);

    return 0;
}

static int
_zic_state_clear(PyObject* module)
{
    _zic_module_state* rec = _zic_state(module);

    Py_CLEAR(rec->specification_base_class);
    Py_CLEAR(rec->object_specification_descriptor_class);
    Py_CLEAR(rec->class_provides_base_class);
    Py_CLEAR(rec->interface_base_class);
    Py_CLEAR(rec->lookup_base_class);
    Py_CLEAR(rec->verifying_base_class);
    Py_CLEAR(rec->adapter_hooks);

    Py_CLEAR(rec->builtin_impl_specs);
    Py_CLEAR(rec->empty);
    Py_CLEAR(rec->fallback);
    Py_CLEAR(rec->implements_class);

    return 0;
}

static _zic_module_state*
_zic_state_load_declarations(PyObject* module)
{
    PyObject* declarations;
    PyObject* builtin_impl_specs;
    PyObject* empty;
    PyObject* fallback;
    PyObject* implements;

    _zic_module_state* rec = _zic_state(module);

    if (!rec->decl_imported) {
        declarations = PyImport_ImportModule("zope.interface.declarations");
        if (declarations == NULL) {
            return NULL;
        }

        builtin_impl_specs = PyObject_GetAttrString(
          declarations, "BuiltinImplementationSpecifications");
        if (builtin_impl_specs == NULL) {
            return NULL;
        }

        empty = PyObject_GetAttrString(declarations, "_empty");
        if (empty == NULL) {
            return NULL;
        }

        fallback =
          PyObject_GetAttrString(declarations, "implementedByFallback");
        if (fallback == NULL) {
            return NULL;
        }

        implements = PyObject_GetAttrString(declarations, "Implements");
        if (implements == NULL) {
            return NULL;
        }

        if (!PyType_Check(implements)) {
            PyErr_SetString(
              PyExc_TypeError,
              "zope.interface.declarations.Implements is not a type");
            return NULL;
        }

        Py_DECREF(declarations);

        rec->builtin_impl_specs = builtin_impl_specs;
        rec->empty = empty;
        rec->fallback = fallback;
        rec->implements_class = (PyTypeObject*)implements;
        rec->decl_imported = 1;
    }
    return rec;
}

static struct PyModuleDef _zic_module;

static PyObject*
implementedByFallback(PyObject* module, PyObject* cls)
{
    _zic_module_state* rec = _zic_state_load_declarations(module);
    if (rec == NULL) { return NULL; }

    return PyObject_CallFunctionObjArgs(rec->fallback, cls, NULL);
}

static char implementedBy___doc__[] =
  ("Interfaces implemented by a class or factory.\n"
   "Raises TypeError if argument is neither a class nor a callable.");

static PyObject*
implementedBy(PyObject* module, PyObject* cls)
{
    /* Fast retrieval of implements spec, if possible, to optimize
       common case.  Use fallback code if we get stuck.
    */
    PyObject *dict = NULL;
    PyObject *spec;

    _zic_module_state* rec = _zic_state_load_declarations(module);
    if (rec == NULL) { return NULL; }

    if (PyObject_TypeCheck(cls, &PySuper_Type)) {
        // Let merging be handled by Python.
        return implementedByFallback(module, cls);
    }

    if (PyType_Check(cls)) {
        dict = TYPE(cls)->tp_dict;
        Py_XINCREF(dict);
    }

    if (dict == NULL)
        dict = PyObject_GetAttrString(cls, "__dict__");

    if (dict == NULL) {
        /* Probably a security proxied class, use more expensive fallback code
         */
        PyErr_Clear();
        return implementedByFallback(module, cls);
    }

    spec = PyObject_GetItem(dict, str__implemented__);
    Py_DECREF(dict);
    if (spec) {

        if (PyObject_TypeCheck(spec, rec->implements_class))
            return spec;

        /* Old-style declaration, use more expensive fallback code */
        Py_DECREF(spec);
        return implementedByFallback(module, cls);
    }

    PyErr_Clear();

    /* Maybe we have a builtin */
    spec = PyDict_GetItem(rec->builtin_impl_specs, cls);
    if (spec != NULL) {
        Py_INCREF(spec);
        return spec;
    }

    /* We're stuck, use fallback */
    return implementedByFallback(module, cls);
}

static char getObjectSpecification___doc__[] =
  ("Get an object's interfaces (internal api)");

static PyObject*
getObjectSpecification(PyObject* module, PyObject* ob)
{
    PyObject *cls;
    PyObject *result;

    _zic_module_state* rec = _zic_state_load_declarations(module);
    if (rec == NULL) { return NULL; }

    result = PyObject_GetAttrString(ob, "__provides__");
    if (!result) {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
            /* Propagate non AttributeError exceptions. */
            return NULL;
        }
        PyErr_Clear();
    } else {
        int is_instance = -1;
        is_instance =
          PyObject_IsInstance(result, OBJECT(rec->specification_base_class));
        if (is_instance < 0) {
            /* Propagate all errors */
            return NULL;
        }
        if (is_instance) {
            return result;
        } else {
        }
    }

    /* We do a getattr here so as not to be defeated by proxies */
    cls = PyObject_GetAttrString(ob, "__class__");
    if (cls == NULL) {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
            /* Propagate non-AttributeErrors */
            return NULL;
        }
        PyErr_Clear();

        Py_INCREF(rec->empty);
        return rec->empty;
    }
    result = implementedBy(module, cls);
    Py_DECREF(cls);

    return result;
}

static char providedBy___doc__[] = ("Get an object's interfaces");

static PyObject*
providedBy(PyObject* module, PyObject* ob)
{
    PyObject *result = NULL;
    PyObject *cls;
    PyObject *cp;
    int is_instance = -1;

    is_instance = PyObject_IsInstance(ob, (PyObject*)&PySuper_Type);
    if (is_instance < 0) {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
            /* Propagate non-AttributeErrors */
            return NULL;
        }
        PyErr_Clear();
    }
    if (is_instance) {
        return implementedBy(module, ob);
    }

    result = PyObject_GetAttrString(ob, "__providedBy__");

    if (result == NULL) {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError)) {
            return NULL;
        }

        PyErr_Clear();
        return getObjectSpecification(module, ob);
    }

    /* We want to make sure we have a spec. We can't do a type check
       because we may have a proxy, so we'll just try to get the
       only attribute.
    */
    if (PyObject_TypeCheck(result, &SpecificationBaseType) ||
        PyObject_HasAttrString(result, "extends"))
        return result;

    /*
      The object's class doesn't understand descriptors.
      Sigh. We need to get an object descriptor, but we have to be
      careful.  We want to use the instance's __provides__,l if
      there is one, but only if it didn't come from the class.
    */
    Py_DECREF(result);

    cls = PyObject_GetAttrString(ob, "__class__");
    if (cls == NULL)
        return NULL;

    result = PyObject_GetAttrString(ob, "__provides__");
    if (result == NULL) {
        /* No __provides__, so just fall back to implementedBy */
        PyErr_Clear();
        result = implementedBy(module, cls);
        Py_DECREF(cls);
        return result;
    }

    cp = PyObject_GetAttrString(cls, "__provides__");
    if (cp == NULL) {
        /* The the class has no provides, assume we're done: */
        PyErr_Clear();
        Py_DECREF(cls);
        return result;
    }

    if (cp == result) {
        /*
          Oops, we got the provides from the class. This means
          the object doesn't have it's own. We should use implementedBy
        */
        Py_DECREF(result);
        result = implementedBy(module, cls);
    }

    Py_DECREF(cls);
    Py_DECREF(cp);

    return result;
}

static struct PyMethodDef m_methods[] = {
    { "implementedBy",
      (PyCFunction)implementedBy,
      METH_O,
      implementedBy___doc__ },
    { "getObjectSpecification",
      (PyCFunction)getObjectSpecification,
      METH_O,
      getObjectSpecification___doc__ },
    { "providedBy", (PyCFunction)providedBy, METH_O, providedBy___doc__ },

    { NULL, (PyCFunction)NULL, 0, NULL } /* sentinel */
};

static char module_doc[] = "C optimizations for zope.interface\n\n";

static struct PyModuleDef _zic_module = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_zope_interface_coptimizations",
    .m_doc = module_doc,
    .m_size = sizeof(_zic_module_state),
    .m_methods = m_methods,
    /*.m_slots=m_slots,*/
    .m_traverse = _zic_state_traverse,
    .m_clear = _zic_state_clear,
};

/*
 *  Provide access to the current module given the type.
 *
 *  At the moment, this just returns the static, but we can adjust this
 *  to do the lookup using 'PyType_GetModuleByDef' (for slot methods)
 *  or via the '*defining_class' arg passed to the yet-to-be-refactored
 *  normal methods declared using 'PyCMethod' calling convention.
 */
static PyObject*
_get_module(PyTypeObject *typeobj)
{
    if (PyType_Check(typeobj)) {
        return PyState_FindModule(&_zic_module);
    }
    PyErr_SetString(PyExc_TypeError, "_get_module: called w/ non-type");
    return NULL;
}

static PyObject*
init(void)
{
    PyObject* module;

#define DEFINE_STRING(S)                                                       \
    if (!(str##S = PyUnicode_FromString(#S)))                                  \
    return NULL

    DEFINE_STRING(__implemented__);
    DEFINE_STRING(_call_conform);
    DEFINE_STRING(_uncached_lookup);
    DEFINE_STRING(_uncached_lookupAll);
    DEFINE_STRING(_uncached_subscriptions);
    DEFINE_STRING(changed);
    DEFINE_STRING(__adapt__);
#undef DEFINE_STRING

    /*
     * To be replaced by a call to PyModuleDef_Init(&_zic_module);
     * the function will just return the initilized module def structure,
     * allowing the interpreter to create a new module instance
     */
    module = PyModule_Create(&_zic_module);
    if (module == NULL)
        return NULL;

    /*
     *  Below this point, the rest of the function will move to
     *  the 'mod_exec' phase (run only after the interpreter has
     *  created the new module instance).
     */

    _zic_module_state* rec = _zic_state_init(module);

    rec->adapter_hooks = PyList_New(0);
    if (rec->adapter_hooks == NULL)
        return NULL;

    /* temporary:  initialize the global static until we can rewire
     * the code using it to use module state.
     */
    adapter_hooks = rec->adapter_hooks;

    /* Initialize types:
     * Static types are only here until we complete the module state /
     * multi-phase initializtion bit.
     */
    SpecificationBaseType.tp_new = PyBaseObject_Type.tp_new;
    if (PyType_Ready(&SpecificationBaseType) < 0)
        return NULL;
    rec->specification_base_class = &SpecificationBaseType;

    OSDType.tp_new = PyBaseObject_Type.tp_new;
    if (PyType_Ready(&OSDType) < 0)
        return NULL;
    rec->object_specification_descriptor_class = &OSDType;

    CPBType.tp_new = PyBaseObject_Type.tp_new;
    if (PyType_Ready(&CPBType) < 0)
        return NULL;
    rec->class_provides_base_class = &CPBType;

    InterfaceBaseType.tp_new = PyBaseObject_Type.tp_new;
    if (PyType_Ready(&InterfaceBaseType) < 0)
        return NULL;
    rec->interface_base_class = &InterfaceBaseType;

    LookupBase.tp_new = PyBaseObject_Type.tp_new;
    if (PyType_Ready(&LookupBase) < 0)
        return NULL;
    rec->lookup_base_class = &LookupBase;

    VerifyingBase.tp_new = PyBaseObject_Type.tp_new;
    if (PyType_Ready(&VerifyingBase) < 0)
        return NULL;
    rec->verifying_base_class = &VerifyingBase;

    /* Add types to our dict FBO python;  also the adapter hooks */
    if (PyModule_AddObject(module,
        "SpecificationBase", OBJECT(rec->specification_base_class)) < 0)
        return NULL;

    if (PyModule_AddObject(module,
        "ObjectSpecificationDescriptor",
        OBJECT(rec->object_specification_descriptor_class)) <
        0)
        return NULL;

    if (PyModule_AddObject(module,
        "ClassProvidesBase", OBJECT(rec->class_provides_base_class)) < 0)
        return NULL;

    if (PyModule_AddObject(module,
        "InterfaceBase", OBJECT(rec->interface_base_class)) < 0)
        return NULL;

    if (PyModule_AddObject(module,
        "LookupBase", OBJECT(rec->lookup_base_class)) < 0)
        return NULL;

    if (PyModule_AddObject(module,
        "VerifyingBase", OBJECT(rec->verifying_base_class)) < 0)
        return NULL;

    if (PyModule_AddObject(module, "adapter_hooks", adapter_hooks) < 0)
        return NULL;

    return module;
}

PyMODINIT_FUNC
PyInit__zope_interface_coptimizations(void)
{
    return init();
}

#ifdef __clang__
#pragma clang diagnostic pop
#endif
