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

#define ASSURE_DICT(N) if (N == NULL) { N = PyDict_New(); \
                                        if (N == NULL) return NULL; \
                                       }


#define LOG(msg) printf((msg))


/* Static strings, used to invoke PyObject_CallMethodObjArgs */
static PyObject *str_call_conform;
static PyObject *str_uncached_lookup;
static PyObject *str_uncached_lookupAll;
static PyObject *str_uncached_subscriptions;
static PyObject *strchanged;
static PyObject *str__adapt__;


/*
 * Utility: fetch thd module the current type, using the module spec.
 */
static PyObject* _get_module(PyTypeObject *typeobj);   /* forward */

/*
 *  Module-scope functions:  forward declared
 */
static PyObject *
implementedByFallback(PyObject* module, PyObject *cls);
static PyObject *
implementedBy(PyObject* module, PyObject *cls);
static PyObject *
getObjectSpecification(PyObject *module, PyObject *ob);
static PyObject *
providedBy(PyObject *module, PyObject *ob);

/*
 * SpecificationBase layout
 */
typedef struct {
    PyObject_HEAD
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
} SpecBase;

static int
SpecBase_traverse(SpecBase* self, visitproc visit, void* arg)
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
SpecBase_clear(SpecBase* self)
{
    Py_CLEAR(self->_implied);
    Py_CLEAR(self->_dependents);
    Py_CLEAR(self->_bases);
    Py_CLEAR(self->_v_attrs);
    Py_CLEAR(self->__iro__);
    Py_CLEAR(self->__sro__);
    return 0;
}

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static void
SpecBase_dealloc(SpecBase* self)
{
    PyTypeObject *tp = Py_TYPE(self);
    PyObject_GC_UnTrack((PyObject *)self);
    SpecBase_clear(self);
    tp->tp_free(OBJECT(self));
    Py_DECREF(tp);
}

/*
 * SpecificationBase methods
 */

static char SpecBase_extends__doc__[] =
"Test whether a specification is or extends another";

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
SpecBase_extends(SpecBase *self, PyObject *other)
{
    PyObject *implied;

    implied = self->_implied;
    if (implied == NULL) { return NULL; }

    if (PyDict_GetItem(implied, other) != NULL) { Py_RETURN_TRUE; }
    else { Py_RETURN_FALSE; }
}

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
SpecBase_call(SpecBase *self, PyObject *args, PyObject *kw)
{
    PyObject *spec;

    if (! PyArg_ParseTuple(args, "O", &spec))
    {
        return NULL;
    }

    return SpecBase_extends(self, spec);
}

static char SpecBase_providedBy__doc__[] =
"Test whether an interface is implemented by the specification";

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
SpecBase_providedBy(PyObject *self, PyObject *ob)
{
    PyObject *decl;
    PyObject *item;
    PyObject *module;
    PyObject *SpecificationBaseClass;

    LOG("SpecBase_providedBy: BEGIN");
    module = _get_module(Py_TYPE(self));

    decl = providedBy(module, ob);
    if (decl == NULL) { return NULL; }

    SpecificationBaseClass = PyObject_GetAttrString(
        module, "SpecificationBase");

    if (PyObject_TypeCheck(decl, (PyTypeObject*)SpecificationBaseClass))
    {
        LOG("SpecBase_providedBy: decl is SpecBase");
        item = SpecBase_extends((SpecBase*)decl, self);
    }
    else
    {
        /* decl is probably a security proxy.  We have to go the long way
        around.
        */
        LOG("SpecBase_providedBy: decl is not SpecBase;  fall back");
        item = PyObject_CallFunctionObjArgs(decl, self, NULL);
    }

    Py_DECREF(decl);
    LOG("SpecBase_providedBy: OK");
    return item;
}

static char SpecBase_implementedBy__doc__[] =
"Test whether the specification is implemented by a class or factory.\n"
"Raise TypeError if argument is neither a class nor a callable.";

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
SpecBase_implementedBy(PyObject *self, PyObject *cls)
{
    PyObject *decl;
    PyObject *item;
    PyObject *module;
    PyObject *SpecificationBaseClass;

    LOG("SpecBase_implementedBy: BEGIN");
    module = _get_module(Py_TYPE(self));

    decl = implementedBy(module, cls);
    if (decl == NULL) { return NULL; }

    SpecificationBaseClass = PyObject_GetAttrString(
        module, "SpecificationBase");

    if (PyObject_TypeCheck(decl, (PyTypeObject*)SpecificationBaseClass))
    {
        item = SpecBase_extends((SpecBase*)decl, self);
    }
    else
    {
        item = PyObject_CallFunctionObjArgs(decl, self, NULL);
    }

    Py_DECREF(decl);
    LOG("SpecBase_implementedBy: OK");
    return item;
}

static struct PyMethodDef SpecBase_methods[] = {
    {"providedBy",
        (PyCFunction)SpecBase_providedBy,
        METH_O,
        SpecBase_providedBy__doc__
    },
    {"implementedBy",
        (PyCFunction)SpecBase_implementedBy,
        METH_O,
        SpecBase_implementedBy__doc__
    },
    {"isOrExtends",
        (PyCFunction)SpecBase_extends,
        METH_O,
        SpecBase_extends__doc__
    },
    {NULL, NULL}           /* sentinel */
};

static PyMemberDef SpecBase_members[] = {
    {"_implied",    T_OBJECT_EX, offsetof(SpecBase, _implied),      0, ""},
    {"_dependents", T_OBJECT_EX, offsetof(SpecBase, _dependents),   0, ""},
    {"_bases",      T_OBJECT_EX, offsetof(SpecBase, _bases),        0, ""},
    {"_v_attrs",    T_OBJECT_EX, offsetof(SpecBase, _v_attrs),      0, ""},
    {"__iro__",     T_OBJECT_EX, offsetof(SpecBase, __iro__),       0, ""},
    {"__sro__",     T_OBJECT_EX, offsetof(SpecBase, __sro__),       0, ""},
    {NULL},
};

/*
 * Heap-based type: SpecificationBase
 */
static PyType_Slot SpecBase_type_slots[] = {
  {Py_tp_dealloc,   SpecBase_dealloc},
  {Py_tp_call,      SpecBase_call},
  {Py_tp_traverse,  SpecBase_traverse},
  {Py_tp_clear,     SpecBase_clear},
  {Py_tp_methods,   SpecBase_methods},
  {Py_tp_members,   SpecBase_members},
  {0,               NULL}
};

static PyType_Spec SpecBase_type_spec = {
  .name="zope.interface.interface.SpecificationBase",
  .basicsize=sizeof(SpecBase),
  .flags=Py_TPFLAGS_DEFAULT |
         Py_TPFLAGS_BASETYPE |
         Py_TPFLAGS_HAVE_GC |
         Py_TPFLAGS_MANAGED_WEAKREF,
  .slots=SpecBase_type_slots
};


/*
 * ObjectSpecificationDescriptor methods
 */
#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
ObjSpedDescr_descr_get(PyObject *self, PyObject *inst, PyObject *cls)
{
    PyObject *module;
    PyObject *provides;

    LOG("ObjSpedDescr_descr_get: BEGIN\n");

    module = _get_module(Py_TYPE(self));
    if(module == NULL) {
        LOG("ObjSpedDescr_descr_get: failed to find module\n");
        return NULL;
    }

    LOG("ObjSpedDescr_descr_get: got module\n");
    if (inst == NULL)
    {
        LOG("ObjSpedDescr_descr_get: no instance, use gOS on class\n");
        return getObjectSpecification(module, cls);
    }

    LOG("ObjSpedDescr_descr_get: fetching __provides__\n");
    provides = PyObject_GetAttrString(inst, "__provides__\n");
    /* Return __provides__ if we got it;
     * otherwise return NULL and propagate non-AttributeError.
    * */
    if (provides != NULL)
    {
        LOG("ObjSpedDescr_descr_get: got instance __provides__\n");
        return provides;
    }
    if (!PyErr_ExceptionMatches(PyExc_AttributeError))
    {
        return NULL;
    }

    PyErr_Clear();
    LOG("ObjSpedDescr_descr_get: no __provides__, "
        "use implementedBy on class\n");
    return implementedBy(module, cls);
}

/*
 * Heap type: ObjectSpecificationDescriptor
 */
static PyType_Slot ObjSpedDescr_type_slots[] = {
  {Py_tp_descr_get,     ObjSpedDescr_descr_get},
  {0,                   NULL}
};

static PyType_Spec ObjSpecDescr_type_spec = {
  .name="_interface_coptimizations.ObjectSpecificationDescriptor",
  .basicsize=0,
  .flags=Py_TPFLAGS_DEFAULT |
         Py_TPFLAGS_BASETYPE |
         Py_TPFLAGS_MANAGED_WEAKREF,
  .slots=ObjSpedDescr_type_slots
};


/*
 * ClassProvidesBase layout
 */
typedef struct {
    SpecBase spec;
    /* These members are handled generically, as for SpecBase members. */
    PyObject* _cls;
    PyObject* _implements;
} ClsPrvBase;

static int
ClsPrvBase_traverse(ClsPrvBase* self, visitproc visit, void* arg)
{
    Py_VISIT(self->_cls);
    Py_VISIT(self->_implements);
    return SpecBase_traverse((SpecBase*)self, visit, arg);
}

static int
ClsPrvBase_clear(ClsPrvBase* self)
{
    Py_CLEAR(self->_cls);
    Py_CLEAR(self->_implements);
    SpecBase_clear((SpecBase*)self);
    return 0;
}

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static void
ClsPrvBase_dealloc(ClsPrvBase* self)
{
    PyObject_GC_UnTrack((PyObject *)self);
    ClsPrvBase_clear(self);
    SpecBase_dealloc((SpecBase*)self);
}

/*
 * ClassProvidesBase methods
 */
#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
ClsPrvBase_descr_get(ClsPrvBase *self, PyObject *inst, PyObject *cls)
{
    PyObject *implements;

    if (self->_cls == NULL)
    {
        PyErr_SetString(
            PyExc_TypeError, "ClsPrvBase_descr_get: no class for descriptor"
        );
        return NULL;
    }

    if (cls == self->_cls)
    {
        if (inst == NULL)
        {
            LOG("ClsPrvBase_descr_get: descr class is cls, w/o instance\n");
            Py_INCREF(self);
            return OBJECT(self);
        }

        LOG("ClsPrvBase_descr_get: descr class is cls, w/ instance\n");
        implements = self->_implements;
        Py_XINCREF(implements);
        return implements;
    }

    PyErr_SetString(PyExc_AttributeError, "__provides__");
    return NULL;
}

static PyMemberDef ClsPrvBase_members[] = {
  {"_cls",
        T_OBJECT_EX, offsetof(ClsPrvBase, _cls),
        0, "Defining class."},
  {"_implements",
        T_OBJECT_EX, offsetof(ClsPrvBase, _implements),
        0, "Result of implementedBy."},
  {NULL}
};

/*
 * Heap type: ClassProvidesBase
 */
static PyType_Slot ClsPrvBase_type_slots[] = {
  {Py_tp_dealloc,   ClsPrvBase_dealloc},
  {Py_tp_traverse,  ClsPrvBase_traverse},
  {Py_tp_clear,     ClsPrvBase_clear},
  {Py_tp_members,   ClsPrvBase_members},
  {Py_tp_descr_get, ClsPrvBase_descr_get},
  /* tp_base cannot be set as a stot -- pass to PyType_FromModuleAndSpec */
  {0,               NULL}
};

static PyType_Spec ClsPrvBase_type_spec = {
  .name="zope.interface.interface.ClassProvidesBase",
  .basicsize=sizeof(ClsPrvBase),
  .flags=Py_TPFLAGS_DEFAULT |
         Py_TPFLAGS_BASETYPE |
         Py_TPFLAGS_HAVE_GC |
         Py_TPFLAGS_MANAGED_WEAKREF,
  .slots=ClsPrvBase_type_slots
};


/*
 *  InterfaceBase layout
 */
typedef struct {
    SpecBase spec;
    PyObject* __name__;
    PyObject* __module__;
    Py_hash_t _v_cached_hash;
} IfaceBase;


static int
IfaceBase_traverse(IfaceBase* self, visitproc visit, void* arg)
{
    Py_VISIT(self->__name__);
    Py_VISIT(self->__module__);
    return SpecBase_traverse((SpecBase*)self, visit, arg);
}

static int
IfaceBase_clear(IfaceBase* self)
{
    Py_CLEAR(self->__name__);
    Py_CLEAR(self->__module__);
    return SpecBase_clear((SpecBase*)self);
}

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static void
IfaceBase_dealloc(IfaceBase* self)
{
    PyObject_GC_UnTrack((PyObject *)self);
    IfaceBase_clear(self);
    SpecBase_dealloc((SpecBase*)self);
}

/*
 * InterfaceBase methods
 */

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
#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
IfaceBase__adapt__(PyObject *self, PyObject *obj)
{
    PyObject *decl;
    PyObject *args;
    PyObject *adapter;
    PyObject *implied;
    PyObject *module;
    PyObject *SpecificationBaseClass;
    PyObject *adapter_hooks;
    PyObject *r;
    int implements;
    int i;
    int l;

    module = _get_module(Py_TYPE(self));
    decl = providedBy(module, obj);
    if (decl == NULL) { return NULL; }

    SpecificationBaseClass = PyObject_GetAttrString(
        module, "SpecificationBase");
    if (PyObject_TypeCheck(decl, (PyTypeObject*)SpecificationBaseClass))
    {
        implied = ((SpecBase*)decl)->_implied;
        if (implied == NULL)
        {
            Py_DECREF(decl);
            return NULL;
        }

        implements = PyDict_GetItem(implied, self) != NULL;
        Py_DECREF(decl);
    }
    else
    {
        /* decl is probably a security proxy.  Go the long way around. */

        r = PyObject_CallFunctionObjArgs(decl, self, NULL);
        Py_DECREF(decl);

        if (r == NULL) { return NULL; }

        implements = PyObject_IsTrue(r);
        Py_DECREF(r);
    }

    if (implements)
    {
        Py_INCREF(obj);
        return obj;
    }

    adapter_hooks = PyObject_GetAttrString(module, "adapter_hooks");

    l = PyList_GET_SIZE(adapter_hooks);

    args = PyTuple_New(2);
    if (args == NULL) { return NULL; }

    Py_INCREF(self);
    PyTuple_SET_ITEM(args, 0, self);

    Py_INCREF(obj);
    PyTuple_SET_ITEM(args, 1, obj);

    for (i = 0; i < l; i++)
    {
        adapter = PyObject_CallObject(
            PyList_GET_ITEM(adapter_hooks, i), args
        );
        if (adapter == NULL || adapter != Py_None)
        {
            Py_DECREF(args);
            return adapter;
        }
        Py_DECREF(adapter);
    }

    Py_DECREF(args);

    Py_INCREF(Py_None);
    return Py_None;
}

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
#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
IfaceBase__call__(PyObject *self, PyObject *args, PyObject *kwargs)
{
    PyObject *conform;
    PyObject *obj;
    PyObject *alternate;
    PyObject *adapter;
    static char *kwlist[] = {"obj", "alternate", NULL};

    conform = obj = alternate = adapter = NULL;

    if (!PyArg_ParseTupleAndKeywords(
            args, kwargs, "O|O", kwlist, &obj, &alternate))
    {
        return NULL;
    }

    conform = PyObject_GetAttrString(obj, "__conform__");
    if (conform == NULL)
    {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError))
        {
            /* Propagate non-AttributeErrors */
            return NULL;
        }
        PyErr_Clear();

        Py_INCREF(Py_None);
        conform = Py_None;
    }

    if (conform != Py_None)
    {
        adapter = PyObject_CallMethodObjArgs(
            self, str_call_conform, conform, NULL);
        Py_DECREF(conform);

        if (adapter == NULL || adapter != Py_None)
        {
            return adapter;
        }
        Py_DECREF(adapter);
    }
    else
    {
        Py_DECREF(conform);
    }

    /* We differ from the Python code here. For speed, instead of always
     * calling self.__adapt__(), we check to see if the type has defined
     * it. Checking in the dict for __adapt__ isn't sufficient because
     * there's no cheap way to tell if it's the __adapt__ that
     * InterfaceBase itself defines (our type will *never* be InterfaceBase,
     * we're always subclassed by InterfaceClass).
     *
     * Instead, we cooperate with InterfaceClass in Python to
     * set a flag in a new subclass when this is necessary.
     * */
    if (PyDict_GetItemString(self->ob_type->tp_dict, "_CALL_CUSTOM_ADAPT"))
    {
        /* Doesn't matter what the value is. Simply being present is enough. */
        adapter = PyObject_CallMethodObjArgs(self, str__adapt__, obj, NULL);
    }
    else
    {
        adapter = IfaceBase__adapt__(self, obj);
    }

    if (adapter == NULL || adapter != Py_None)
    {
        return adapter;
    }
    Py_DECREF(adapter);

    if (alternate != NULL)
    {
        Py_INCREF(alternate);
        return alternate;
    }

    adapter = Py_BuildValue("sOO", "Could not adapt", obj, self);
    if (adapter != NULL)
    {
        PyErr_SetObject(PyExc_TypeError, adapter);
        Py_DECREF(adapter);
    }
    return NULL;
}

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static Py_hash_t
IfaceBase_hash(IfaceBase* self)
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


#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject*
IfaceBase_richcompare(IfaceBase* self, PyObject* other, int op)
{
    PyObject* othername;
    PyObject* othermod;
    PyObject* oresult;
    IfaceBase* otherib;
    int result;

    LOG("IfaceBase_richcompare: START\n");
    otherib = NULL;
    oresult = othername = othermod = NULL;

    if (OBJECT(self) == other) {
        LOG("IfaceBase_richcompare: compare with self\n");
        switch(op) {
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
        LOG("IfaceBase_richcompare: compare with None\n");
        switch(op) {
        case Py_LT:
        case Py_LE:
        case Py_NE:
            Py_RETURN_TRUE;
        default:
            Py_RETURN_FALSE;
        }
    }

    if (PyObject_TypeCheck(other, Py_TYPE(self))) {
        // This branch borrows references. No need to clean
        // up if otherib is not null.
        LOG("IfaceBase_richcompare: compare with same type\n");
        otherib = (IfaceBase*)other;
        othername = otherib->__name__;
        othermod = otherib->__module__;
    }
    else {
        LOG("IfaceBase_richcompare: compare with another type\n");
        othername = PyObject_GetAttrString(other, "__name__");
        if (othername) {
            othermod = PyObject_GetAttrString(other, "__module__");
        }
        if (!othername || !othermod) {
            if (PyErr_Occurred() &&
                PyErr_ExceptionMatches(PyExc_AttributeError))
            {
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
    LOG("IfaceBase_richcompare: comparing name and module\n");
    result = PyObject_RichCompareBool(self->__name__, othername, Py_EQ);
    if (result == 0) {
        result = PyObject_RichCompareBool(self->__name__, othername, op);
    }
    else if (result == 1) {
        result = PyObject_RichCompareBool(self->__module__, othermod, op);
    }
    // If either comparison failed, we have an error set.
    // Leave oresult NULL so we raise it.
    if (result == -1) {
        goto cleanup;
    }

    LOG("IfaceBase_richcompare: END OK\n");
    oresult = result ? Py_True : Py_False;


cleanup:
    Py_XINCREF(oresult);

    if (!otherib) {
        Py_XDECREF(othername);
        Py_XDECREF(othermod);
    }
    return oresult;

}

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static int
IfaceBase_init(IfaceBase* self, PyObject* args, PyObject* kwargs)
{
    PyObject* module = NULL;
    PyObject* name = NULL;
    static char *kwlist[] = {"__name__", "__module__", NULL};

    if (!PyArg_ParseTupleAndKeywords(
        args, kwargs,
        "|OO:InterfaceBase.__init__",
        kwlist, &name, &module)) {
        return -1;
    }
    IfaceBase_clear(self);
    if (module == Py_None)
    {
        LOG("IfaceBase_init:  __module__ is None\n");
        return -1;
    }
    module = module ? module : Py_None;
    self->__module__ = module;
    Py_INCREF(self->__module__);
    name = name ? name : Py_None;
    self->__name__ = name;
    Py_INCREF(self->__name__);
    return 0;
}

static PyMemberDef IfaceBase_members[] = {
    {"__name__",
        T_OBJECT_EX, offsetof(IfaceBase, __name__),   0, ""},
    // The redundancy between __module__ and __ibmodule__ is because
    // __module__ is often shadowed by subclasses.
    {"__module__",
        T_OBJECT_EX, offsetof(IfaceBase, __module__), READONLY, ""},
    {"__ibmodule__",
        T_OBJECT_EX, offsetof(IfaceBase, __module__), 0, ""},
    {NULL}
};

static struct PyMethodDef IfaceBase_methods[] = {
    {"__adapt__",
        (PyCFunction)IfaceBase__adapt__,
        METH_O, "Adapt an object to the receiver"},
    {NULL, NULL} /* sentinel */
};

/*
 * Heap type: InterfaceBase
 */
static PyType_Slot ib_type_slots[] = {
  {Py_tp_dealloc,       IfaceBase_dealloc},
  {Py_tp_hash,          IfaceBase_hash},
  {Py_tp_call,          IfaceBase__call__},
  {Py_tp_traverse,      IfaceBase_traverse},
  {Py_tp_clear,         IfaceBase_clear},
  {Py_tp_richcompare,   IfaceBase_richcompare},
  {Py_tp_methods,       IfaceBase_methods},
  {Py_tp_members,       IfaceBase_members},
  {Py_tp_init,          IfaceBase_init},
  /* tp_base cannot be set as a stot -- pass to PyType_FromModuleAndSpec */
  {0,                   NULL}
};

static PyType_Spec InterfaceBaseSpec = {
  .name="zope.interface.interface.InterfaceBase",
  .basicsize=sizeof(IfaceBase),
  .flags=Py_TPFLAGS_DEFAULT |
         Py_TPFLAGS_BASETYPE |
         Py_TPFLAGS_HAVE_GC |
         Py_TPFLAGS_MANAGED_WEAKREF,
  .slots=ib_type_slots
};

/*
 * LookupBase layout
 */
typedef struct {
  PyObject_HEAD
  PyObject *_cache;
  PyObject *_mcache;
  PyObject *_scache;
} LkpBase;

static int
LkpBase_traverse(LkpBase *self, visitproc visit, void *arg)
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
LkpBase_clear(LkpBase *self)
{
    Py_CLEAR(self->_cache);
    Py_CLEAR(self->_mcache);
    Py_CLEAR(self->_scache);
    return 0;
}

static void
LkpBase_dealloc(LkpBase *self)
{
    PyTypeObject *tp = Py_TYPE(self);
    PyObject_GC_UnTrack((PyObject *)self);
    LkpBase_clear(self);
    tp->tp_free((PyObject*)self);
    Py_DECREF(tp);
}

/*
 * LookupBase methods
 */
/*
    def changed(self, ignored=None):
        self._cache.clear()
        self._mcache.clear()
        self._scache.clear()
*/
static PyObject *
LkpBase_changed(LkpBase *self, PyObject *ignored)
{
    LkpBase_clear(self);
    Py_INCREF(Py_None);
    return Py_None;
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

static PyObject *
_subcache(PyObject *cache, PyObject *key)
{
    PyObject *subcache;
    int status;

    subcache = PyDict_GetItem(cache, key);
    if (subcache == NULL)
    {
        subcache = PyDict_New();
        if (subcache == NULL) { return NULL; }

        status = PyDict_SetItem(cache, key, subcache);
        Py_DECREF(subcache);
        if (status < 0) { return NULL; }
    }

    return subcache;
}

static PyObject *
_getcache(LkpBase *self, PyObject *provided, PyObject *name)
{
    PyObject *cache;

    ASSURE_DICT(self->_cache);

    cache = _subcache(self->_cache, provided);
    if (cache == NULL) { return NULL; }

    if (name != NULL && PyObject_IsTrue(name))
    {
        cache = _subcache(cache, name);
    }

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

static PyObject *
_lookup(LkpBase *self,
        PyObject *required, PyObject *provided, PyObject *name,
        PyObject *default_)
{
    PyObject *result;
    PyObject *key;
    PyObject *cache;
    int status;

    result = key = cache = NULL;

    if ( name && !PyUnicode_Check(name) )
    {
        PyErr_SetString(PyExc_ValueError,
                        "name is not a string or unicode");
        return NULL;
    }

    /* If `required` is a lazy sequence, it could have arbitrary side-effects,
        such as clearing our caches. So we must not retrieve the cache until
        after resolving it. */
    required = PySequence_Tuple(required);
    if (required == NULL) { return NULL; }

    cache = _getcache(self, provided, name);
    if (cache == NULL) { return NULL; }

    if (PyTuple_GET_SIZE(required) == 1)
    {
        key = PyTuple_GET_ITEM(required, 0);
    }
    else
    {
        key = required;
    }

    result = PyDict_GetItem(cache, key);
    if (result == NULL)
    {
        result = PyObject_CallMethodObjArgs(
            OBJECT(self), str_uncached_lookup, required, provided, name, NULL
        );
        if (result == NULL)
        {
            Py_DECREF(required);
            return NULL;
        }

        status = PyDict_SetItem(cache, key, result);
        Py_DECREF(required);
        if (status < 0)
        {
            Py_DECREF(result);
            return NULL;
        }
    }
    else
    {
        Py_INCREF(result);
        Py_DECREF(required);
    }

    if (result == Py_None && default_ != NULL)
    {
        Py_DECREF(Py_None);
        Py_INCREF(default_);
        return default_;
    }

    return result;
}

static PyObject *
LkpBase_lookup(LkpBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *required;
    PyObject *provided;
    PyObject *name=NULL;
    PyObject *default_=NULL;
    static char *kwlist[] = {"required", "provided", "name", "default", NULL};

    if (! PyArg_ParseTupleAndKeywords(
            args, kwds,
            "OO|OO:LookupBase.lookup", kwlist,
            &required, &provided, &name, &default_))
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
static PyObject *
_lookup1(LkpBase *self,
        PyObject *required,
        PyObject *provided,
        PyObject *name,
        PyObject *default_)
{
    PyObject *result;
    PyObject *cache;

    if ( name && !PyUnicode_Check(name) )
    {
        PyErr_SetString(PyExc_ValueError,
                        "name is not a string or unicode");
        return NULL;
    }

    cache = _getcache(self, provided, name);
    if (cache == NULL) { return NULL; }

    result = PyDict_GetItem(cache, required);
    if (result == NULL)
    {
        PyObject *tup;

        tup = PyTuple_New(1);
        if (tup == NULL) { return NULL; }

        Py_INCREF(required);
        PyTuple_SET_ITEM(tup, 0, required);
        result = _lookup(self, tup, provided, name, default_);
        Py_DECREF(tup);
    }
    else
    {
        if (result == Py_None && default_ != NULL)
        {
            result = default_;
        }
        Py_INCREF(result);
    }

    return result;
}

static PyObject *
LkpBase_lookup1(LkpBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *required;
    PyObject *provided;
    PyObject *name=NULL;
    PyObject *default_=NULL;
    static char *kwlist[] = {"required", "provided", "name", "default", NULL};

    if (! PyArg_ParseTupleAndKeywords(
            args, kwds,
            "OO|OO:LookupBase.lookup1", kwlist,
            &required, &provided, &name, &default_))
    {
        return NULL;
    }

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
static PyObject *
_adapter_hook(LkpBase *self,
              PyObject *provided,
              PyObject *object,
              PyObject *name,
              PyObject *default_)
{
    PyObject *module;
    PyObject *required;
    PyObject *factory;
    PyObject *result;

    if ( name && !PyUnicode_Check(name) )
    {
        PyErr_SetString(PyExc_ValueError,
                        "name is not a string or unicode");
        return NULL;
    }

    module = _get_module(Py_TYPE(self));
    required = providedBy(module, object);
    if (required == NULL) { return NULL; }

    factory = _lookup1(self, required, provided, name, Py_None);
    Py_DECREF(required);
    if (factory == NULL) { return NULL; }

    if (factory != Py_None)
    {
        if (PyObject_TypeCheck(object, &PySuper_Type))
        {
            PyObject* self = PyObject_GetAttrString(object, "__self__");
            if (self == NULL)
            {
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
        {
            return result;
        }
    }
    else
    {
        result = factory; /* None */
    }

    if (default_ == NULL || default_ == result) /* No default specified, */
    {
        return result;   /* Return None.  result is owned None */
    }

    Py_DECREF(result);
    Py_INCREF(default_);

    return default_;
}

static PyObject *
LkpBase_adapter_hook(LkpBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *object;
    PyObject *provided;
    PyObject *name=NULL;
    PyObject *default_=NULL;
    static char *kwlist[] = {"provided", "object", "name", "default", NULL};

    if (! PyArg_ParseTupleAndKeywords(
            args, kwds,
            "OO|OO:LookupBase.adapter_hook", kwlist,
            &provided, &object, &name, &default_))
    {
        return NULL;
    }

    return _adapter_hook(self, provided, object, name, default_);
}

static PyObject *
LkpBase_queryAdapter(LkpBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *object;
    PyObject *provided;
    PyObject *name=NULL;
    PyObject *default_=NULL;
    static char *kwlist[] = {"object", "provided", "name", "default", NULL};

    if (! PyArg_ParseTupleAndKeywords(
            args, kwds,
            "OO|OO:LookupBase.queryAdapter", kwlist,
            &object, &provided, &name, &default_))
    {
        return NULL;
    }

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
static PyObject *
_lookupAll(LkpBase *self, PyObject *required, PyObject *provided)
{
    PyObject *cache, *result;

    /* resolve before getting cache. See note in _lookup. */
    required = PySequence_Tuple(required);
    if (required == NULL) { return NULL; }

    ASSURE_DICT(self->_mcache);
    cache = _subcache(self->_mcache, provided);
    if (cache == NULL) { return NULL; }

    result = PyDict_GetItem(cache, required);
    if (result == NULL)
    {
        int status;

        result = PyObject_CallMethodObjArgs(
            OBJECT(self), str_uncached_lookupAll, required, provided, NULL);
        if (result == NULL)
        {
            Py_DECREF(required);
            return NULL;
        }

        status = PyDict_SetItem(cache, required, result);
        Py_DECREF(required);
        if (status < 0)
        {
            Py_DECREF(result);
            return NULL;
        }
    }
    else
    {
        Py_INCREF(result);
        Py_DECREF(required);
    }

    return result;
}

static PyObject *
LkpBase_lookupAll(LkpBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *required;
    PyObject *provided;
    static char *kwlist[] = {"required", "provided", NULL};

    if (! PyArg_ParseTupleAndKeywords(
                args, kwds,
                "OO:LookupBase.lookupAll", kwlist,
                &required, &provided))
    {
        return NULL;
    }

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
static PyObject *
_subscriptions(LkpBase *self, PyObject *required, PyObject *provided)
{
    PyObject *cache;
    PyObject *result;

    /* resolve before getting cache. See note in _lookup. */
    required = PySequence_Tuple(required);
    if (required == NULL) { return NULL; }

    ASSURE_DICT(self->_scache);
    cache = _subcache(self->_scache, provided);
    if (cache == NULL) { return NULL; }

    result = PyDict_GetItem(cache, required);
    if (result == NULL)
    {
        int status;

        result = PyObject_CallMethodObjArgs(
                    OBJECT(self), str_uncached_subscriptions,
                    required, provided, NULL);
        if (result == NULL)
        {
            Py_DECREF(required);
            return NULL;
        }
        status = PyDict_SetItem(cache, required, result);
        Py_DECREF(required);
        if (status < 0)
        {
            Py_DECREF(result);
            return NULL;
        }
    }
    else
    {
        Py_INCREF(result);
        Py_DECREF(required);
    }

    return result;
}

static PyObject *
LkpBase_subscriptions(LkpBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *required;
    PyObject *provided;
    static char *kwlist[] = {"required", "provided", NULL};

    if (! PyArg_ParseTupleAndKeywords(
                args, kwds,
                "OO", kwlist,
                &required, &provided))
    {
        return NULL;
    }

    return _subscriptions(self, required, provided);
}

static struct PyMethodDef LookupBase_methods[] = {
    {"changed",
        (PyCFunction)LkpBase_changed,       METH_O,        ""},
    {"lookup",
        (PyCFunction)LkpBase_lookup,        METH_KEYWORDS | METH_VARARGS, ""},
    {"lookup1",
        (PyCFunction)LkpBase_lookup1,       METH_KEYWORDS | METH_VARARGS, ""},
    {"queryAdapter",
        (PyCFunction)LkpBase_queryAdapter,  METH_KEYWORDS | METH_VARARGS, ""},
    {"adapter_hook",
        (PyCFunction)LkpBase_adapter_hook,  METH_KEYWORDS | METH_VARARGS, ""},
    {"lookupAll",
        (PyCFunction)LkpBase_lookupAll,     METH_KEYWORDS | METH_VARARGS, ""},
    {"subscriptions",
        (PyCFunction)LkpBase_subscriptions, METH_KEYWORDS | METH_VARARGS, ""},
    {NULL, NULL}               /* sentinel */
};


/*
 * Heap type: LookupBase
 */
static PyType_Slot LkpBase_type_slots[] = {
    {Py_tp_dealloc,     LkpBase_dealloc},
    {Py_tp_traverse,    LkpBase_traverse},
    {Py_tp_clear,       LkpBase_clear},
    {Py_tp_methods,     LookupBase_methods},
    {0,                 NULL}
};

static PyType_Spec LkpBase_type_spec = {
    .name="zope.interface.interface.LookupBase",
    .basicsize=sizeof(LkpBase),
    .flags=Py_TPFLAGS_DEFAULT |
            Py_TPFLAGS_BASETYPE |
            Py_TPFLAGS_HAVE_GC |
            Py_TPFLAGS_MANAGED_WEAKREF,
    .slots=LkpBase_type_slots
};


/*
 * VerifyingBase layout
 */
typedef struct {
    PyObject_HEAD
    PyObject *_cache;
    PyObject *_mcache;
    PyObject *_scache;
    PyObject *_verify_ro;
    PyObject *_verify_generations;
} VfyBase;

static int
VfyBase_traverse(VfyBase *self, visitproc visit, void *arg)
{
    int vret;

    vret = LkpBase_traverse((LkpBase *)self, visit, arg);
    if (vret != 0) { return vret; }

    if (self->_verify_ro)
    {
        vret = visit(self->_verify_ro, arg);
        if (vret != 0) { return vret; }
    }

    if (self->_verify_generations)
    {
        vret = visit(self->_verify_generations, arg);
        if (vret != 0) { return vret; }
    }

    return 0;
}

static int
VfyBase_clear(VfyBase *self)
{
    LkpBase_clear((LkpBase *)self);
    Py_CLEAR(self->_verify_generations);
    Py_CLEAR(self->_verify_ro);
    return 0;
}


static void
VfyBase_dealloc(VfyBase *self)
{
    PyTypeObject *tp = Py_TYPE(self);
    PyObject_GC_UnTrack((PyObject *)self);
    VfyBase_clear(self);
    tp->tp_free((PyObject*)self);
    Py_DECREF(tp);
}

/*
    def changed(self, originally_changed):
        super(VerifyingBasePy, self).changed(originally_changed)
        self._verify_ro = self._registry.ro[1:]
        self._verify_generations = [r._generation for r in self._verify_ro]
*/
static PyObject *
_generations_tuple(PyObject *ro)
{
    PyObject *generations;
    int i;
    int l;

    l = PyTuple_GET_SIZE(ro);
    generations = PyTuple_New(l);

    for (i=0; i < l; i++)
    {
        PyObject *generation;

        generation = PyObject_GetAttrString(
                        PyTuple_GET_ITEM(ro, i), "_generation");
        if (generation == NULL)
        {
            Py_DECREF(generations);
            return NULL;
        }
        PyTuple_SET_ITEM(generations, i, generation);
    }

    return generations;
}

static PyObject *
VfyBase_changed(VfyBase *self, PyObject *ignored)
{
    PyObject *t;
    PyObject *ro;

    VfyBase_clear(self);

    t = PyObject_GetAttrString(OBJECT(self), "_registry");
    if (t == NULL) { return NULL; }

    ro = PyObject_GetAttrString(t, "ro");
    Py_DECREF(t);
    if (ro == NULL) { return NULL; }

    t = PyObject_CallFunctionObjArgs(OBJECT(&PyTuple_Type), ro, NULL);
    Py_DECREF(ro);
    if (t == NULL) { return NULL; }

    ro = PyTuple_GetSlice(t, 1, PyTuple_GET_SIZE(t));
    Py_DECREF(t);
    if (ro == NULL) { return NULL; }

    self->_verify_generations = _generations_tuple(ro);
    if (self->_verify_generations == NULL)
    {
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
_verify(VfyBase *self)
{
    PyObject *changed_result;
    PyObject *generations;
    int changed;

    if (self->_verify_ro != NULL && self->_verify_generations != NULL)
    {
        generations = _generations_tuple(self->_verify_ro);
        if (generations == NULL) { return -1; }

        changed = PyObject_RichCompareBool(self->_verify_generations,
                                            generations, Py_NE);
        Py_DECREF(generations);

        if (changed == -1) { return -1; }
        if (changed == 0) { return 0; }
    }

    changed_result = PyObject_CallMethodObjArgs(
                            OBJECT(self), strchanged,
                            Py_None, NULL);
    if (changed_result == NULL) { return -1; }

    Py_DECREF(changed_result);
    return 0;
}

static PyObject *
VfyBase_lookup(VfyBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *required;
    PyObject *provided;
    PyObject *name=NULL;
    PyObject *default_=NULL;
    static char *kwlist[] = {"required", "provided", "name", "default", NULL};

    if (! PyArg_ParseTupleAndKeywords(
                args, kwds,
                "OO|OO", kwlist,
                &required, &provided, &name, &default_)
    ) { return NULL; }

    if (_verify(self) < 0) { return NULL; }

    return _lookup((LkpBase *)self, required, provided, name, default_);
}

static PyObject *
VfyBase_lookup1(VfyBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *required;
    PyObject *provided;
    PyObject *name=NULL;
    PyObject *default_=NULL;
    static char *kwlist[] = {"required", "provided", "name", "default", NULL};

    if (! PyArg_ParseTupleAndKeywords(
                args, kwds,
                "OO|OO", kwlist,
                &required, &provided, &name, &default_)
    ) { return NULL; }

    if (_verify(self) < 0) { return NULL; }

    return _lookup1((LkpBase *)self, required, provided, name, default_);
}

static PyObject *
VfyBase_adapter_hook(VfyBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *object;
    PyObject *provided;
    PyObject *name=NULL;
    PyObject *default_=NULL;
    static char *kwlist[] = {"provided", "object", "name", "default", NULL};

    if (! PyArg_ParseTupleAndKeywords(
            args, kwds,
            "OO|OO", kwlist,
            &provided, &object, &name, &default_)
    ) { return NULL; }

    if (_verify(self) < 0) { return NULL; }

    return _adapter_hook((LkpBase *)self, provided, object, name, default_);
}

static PyObject *
VfyBase_queryAdapter(VfyBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *object;
    PyObject *provided;
    PyObject *name=NULL;
    PyObject *default_=NULL;
    static char *kwlist[] = {"object", "provided", "name", "default", NULL};

    if (! PyArg_ParseTupleAndKeywords(
                args, kwds,
                "OO|OO", kwlist,
                &object, &provided, &name, &default_)
    ) { return NULL; }

    if (_verify(self) < 0) { return NULL; }

    return _adapter_hook((LkpBase *)self, provided, object, name, default_);
}

static PyObject *
VfyBase_lookupAll(VfyBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *required;
    PyObject *provided;
    static char *kwlist[] = {"required", "provided", NULL};

    if (! PyArg_ParseTupleAndKeywords(
                args, kwds,
                "OO", kwlist,
                &required, &provided)
    ) { return NULL; }

    if (_verify(self) < 0) { return NULL; }

    return _lookupAll((LkpBase *)self, required, provided);
}

static PyObject *
VfyBase_subscriptions(VfyBase *self, PyObject *args, PyObject *kwds)
{
    PyObject *required;
    PyObject *provided;
    static char *kwlist[] = {"required", "provided", NULL};

    if (! PyArg_ParseTupleAndKeywords(
                args, kwds,
                "OO", kwlist,
                &required, &provided)
    ) { return NULL; }

    if (_verify(self) < 0) { return NULL; }

    return _subscriptions((LkpBase *)self, required, provided);
}

static struct PyMethodDef VfyBase_methods[] = {
    {"changed",
        (PyCFunction)VfyBase_changed,       METH_O,        ""},
    {"lookup",
        (PyCFunction)VfyBase_lookup,        METH_KEYWORDS | METH_VARARGS, ""},
    {"lookup1",
        (PyCFunction)VfyBase_lookup1,       METH_KEYWORDS | METH_VARARGS, ""},
    {"queryAdapter",
        (PyCFunction)VfyBase_queryAdapter,  METH_KEYWORDS | METH_VARARGS, ""},
    {"adapter_hook",
        (PyCFunction)VfyBase_adapter_hook,  METH_KEYWORDS | METH_VARARGS, ""},
    {"lookupAll",
        (PyCFunction)VfyBase_lookupAll,     METH_KEYWORDS | METH_VARARGS, ""},
    {"subscriptions",
        (PyCFunction)VfyBase_subscriptions, METH_KEYWORDS | METH_VARARGS, ""},
    {NULL, NULL}               /* sentinel */
};

/*
 * Heap type: VerifyingBase
 */
static PyType_Slot VfyBase_type_slots[] = {
    {Py_tp_dealloc,     VfyBase_dealloc},
    {Py_tp_traverse,    VfyBase_traverse},
    {Py_tp_clear,       VfyBase_clear},
    {Py_tp_methods,     VfyBase_methods},
    /* tp_base cannot be set as a stot -- pass to PyType_FromModuleAndSpec */
    {0,                 NULL}
};

static PyType_Spec VfyBase_type_spec = {
    .name="zope.interface.interface.VerifyingBase",
    .basicsize=sizeof(VfyBase),
    .flags=Py_TPFLAGS_DEFAULT |
            Py_TPFLAGS_BASETYPE |
            Py_TPFLAGS_HAVE_GC |
            Py_TPFLAGS_MANAGED_WEAKREF,
    .slots=VfyBase_type_slots
};

/*
 * Module state structure
 *
 * imports from 'zope.interface.declarations, plus the 'decl_imported'
 * flag to indicate that import was already complete.
 */
typedef struct{
    int             decl_imported;
    PyObject *      builtin_impl_specs;
    PyObject *      empty;
    PyObject *      fallback;
    PyTypeObject *  Implements;
} _zic_state_rec;

/*
 *  Macro to speed lookup of state members
 */
#define _zic_state(o) ((_zic_state_rec*)PyModule_GetState(o))

static int
_zic_state_init(PyObject *module)
{
    _zic_state(module)->decl_imported = 0;
    _zic_state(module)->builtin_impl_specs = NULL;
    _zic_state(module)->empty = NULL;
    _zic_state(module)->fallback = NULL;
    _zic_state(module)->Implements = NULL;
    return 0;
}

static int
_zic_state_traverse(PyObject *module, visitproc visit, void* arg)
{
    Py_VISIT(_zic_state(module)->builtin_impl_specs);
    Py_VISIT(_zic_state(module)->empty);
    Py_VISIT(_zic_state(module)->fallback);
    Py_VISIT(_zic_state(module)->Implements);
    return 0;
}

static int
_zic_state_clear(PyObject *module)
{
    Py_CLEAR(_zic_state(module)->builtin_impl_specs);
    Py_CLEAR(_zic_state(module)->empty);
    Py_CLEAR(_zic_state(module)->fallback);
    Py_CLEAR(_zic_state(module)->Implements);
    return 0;
}

/*
 * Latched loader for module state
 */
#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static _zic_state_rec*
_zic_state_load(PyObject* module)
{
    LOG("_zic_state_load: BEGIN\n");
    _zic_state_rec *rec = _zic_state(module);
    PyObject *declarations;
    PyObject *builtin_impl_specs;
    PyObject *empty;
    PyObject *fallback;
    PyObject *implements;

    if (! rec->decl_imported)
    {
        LOG("_zic_state_load: importing declarations\n");
        declarations = PyImport_ImportModule("zope.interface.declarations");
        if (declarations == NULL) { return NULL; }

        builtin_impl_specs = PyObject_GetAttrString(
            declarations, "BuiltinImplementationSpecifications"
        );
        if (builtin_impl_specs == NULL) { return NULL; }

        empty = PyObject_GetAttrString(declarations, "_empty");
        if (empty == NULL) { return NULL; }

        fallback = PyObject_GetAttrString(
            declarations, "implementedByFallback");
        if (fallback == NULL) { return NULL; }

        implements = PyObject_GetAttrString(declarations, "Implements");
        if (implements == NULL) { return NULL; }

        if (! PyType_Check(implements))
        {
            PyErr_SetString(
                PyExc_TypeError,
                "zope.interface.declarations.Implements is not a type"
            );
            return NULL;
        }

        Py_DECREF(declarations);

        rec->builtin_impl_specs = builtin_impl_specs;
        rec->empty = empty;
        rec->fallback = fallback;
        rec->Implements = (PyTypeObject*)implements;
        rec->decl_imported = 1;
    }
    LOG("_zic_state_load: END\n");
    return rec;
}


/*
 * Call back into Python to handle complex / slower paths
 *
 * Note that the Python implementation may call back into C, which
 * is a bit of a mess.
 */
#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
implementedByFallback(PyObject* module, PyObject *cls)
{
    PyObject * result;

    LOG("implementedByFallback: getting rec\n");
    _zic_state_rec *rec = _zic_state_load(module);
    if (rec == NULL) { return NULL; }

    LOG("implementedByFallback: calling into Python\n");
    result = PyObject_CallFunctionObjArgs(rec->fallback, cls, NULL);

    LOG("implementedByFallback: returned from Python\n");
    return result;
}

/*
 * Fast retrieval of implements spec, if possible, to optimize
 *  common case.  Use fallback code if we get stuck.
 */
#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
implementedBy(PyObject* module, PyObject *cls)
{
    PyObject *dict = NULL;
    PyObject *spec;

    _zic_state_rec *rec = _zic_state_load(module);
    if (rec == NULL) { return NULL; }

    if (PyObject_TypeCheck(cls, &PySuper_Type))
    {
        /* Let merging be handled by Python. */
        LOG("implementedBy: super, fallback\n");
        return implementedByFallback(module, cls);
    }

    if (PyType_Check(cls))
    {
        LOG("implementedBy: dict from tp_dict\n");
        dict = TYPE(cls)->tp_dict;
        Py_XINCREF(dict);
    }

    if (dict == NULL)
    {
        LOG("implementedBy: dict from __dict__\n");
        dict = PyObject_GetAttrString(cls, "__dict__");
    }

    if (dict == NULL)
    {
        /* Probably a security proxied class, fallback to Python */
        LOG("implementedBy: no dict, fallback\n");
        PyErr_Clear();
        return implementedByFallback(module, cls);
    }

    spec = PyDict_GetItemString(dict, "__implemented__");
    Py_DECREF(dict);

    if (spec)
    {
        if (PyObject_TypeCheck(spec, rec->Implements))
        {
            LOG("implementedBy: spec isinstance Implements, OK\n");
            return spec;
        }

        /* Old-style declaration, use more expensive fallback code */
        Py_DECREF(spec);
        LOG("implementedBy: spec not isinstance Implements, fallback\n");
        return implementedByFallback(module, cls);
    }

    PyErr_Clear();

    spec = PyDict_GetItem(rec->builtin_impl_specs, cls);
    if (spec != NULL)
    {
        LOG("implementedBy: spec found in builtins registry\n");
        Py_INCREF(spec);
        return spec;
    }

    /* We're stuck, use fallback */
    LOG("implementedBy: no spec found, final fallback\n");
    return implementedByFallback(module, cls);
}

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
getObjectSpecification(PyObject *module, PyObject *ob)
{
    PyObject *cls;
    PyObject *result;
    PyObject* SpecificationBaseClass;
    int is_instance;

    _zic_state_rec *rec = _zic_state_load(module);
    if (rec == NULL) { return NULL; }

    result = PyObject_GetAttrString(ob, "__provides__");
    if (!result)
    {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError))
        {
            /* Propagate non AttributeError exceptions. */
            return NULL;
        }
        LOG("getObjectSpecification: ob has no __provides__\n");
        PyErr_Clear();
    }
    else
    {
        SpecificationBaseClass = PyObject_GetAttrString(
            module, "SpecificationBase");
        is_instance = PyObject_IsInstance(result, SpecificationBaseClass);
        if (is_instance < 0)
        {
            /* Propagate all errors */
            return NULL;
        }
        if (is_instance)
        {
            LOG("getObjectSpecification: ob has valid __provides__\n");
            return result;
        }
        else
        {
            LOG("getObjectSpecification: ob has invalid __provides__\n");
        }
    }

    /* We do a getattr here so as not to be defeated by proxies */
    cls = PyObject_GetAttrString(ob, "__class__");
    if (cls == NULL)
    {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError))
        {
            /* Propagate non-AttributeErrors */
            return NULL;
        }
        LOG(
            "getObjectSpecification: couldn't get __class__; "
            "returning empty\n"
        );
        PyErr_Clear();

        Py_INCREF(rec->empty);
        return rec->empty;
    }
    LOG("getObjectSpecification: delegating to implementedBy\n");
    result = implementedBy(module, cls);
    Py_DECREF(cls);

    return result;
}

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject *
providedBy(PyObject *module, PyObject *ob)
{
    PyObject *result;
    PyObject *cls;
    PyObject *cp;
    PyObject* SpecificationBaseClass;
    int is_instance = -1;
    result = NULL;

    is_instance = PyObject_IsInstance(ob, (PyObject*)&PySuper_Type);
    if (is_instance < 0)
    {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError))
        {
            /* Propagate non-AttributeErrors */
            return NULL;
        }
        PyErr_Clear();
    }
    if (is_instance)
    {
        /* Shoudn't this use 'implementedByFallback'? */
        LOG("providedBy: ob is super, delegate to implementedBy\n");
        return implementedBy(module, ob);
    }

    result = PyObject_GetAttrString(ob, "__providedby__");

    if (result == NULL)
    {
        if (!PyErr_ExceptionMatches(PyExc_AttributeError))
        {
            return NULL;
        }

        PyErr_Clear();
        LOG(
            "providedBy: no __providedby__, delegating to "
            "getObjectSpecification\n"
        );
        return getObjectSpecification(module, ob);
    }


    /* We want to make sure we have a spec. We can't do a type check
        because we may have a proxy, so we'll just try to get the
        only attribute.
    */
    SpecificationBaseClass = PyObject_GetAttrString(
        module, "SpecificationBase");

    if (PyObject_TypeCheck(result, (PyTypeObject*)SpecificationBaseClass) ||
        PyObject_HasAttrString(result, "extends"))
    {
        return result;
    }

    /*
        The object's class doesn't understand descriptors.
        Sigh. We need to get an object descriptor, but we have to be
        careful.  We want to use the instance's __provides__,l if
        there is one, but only if it didn't come from the class.
    */
    Py_DECREF(result);

    cls = PyObject_GetAttrString(ob, "__class__");
    if (cls == NULL) { return NULL; }

    result = PyObject_GetAttrString(ob, "__provides__");
    if (result == NULL)
    {
        /* No __provides__, so just fall back to implementedBy */
        PyErr_Clear();
        result = implementedBy(module, cls);

        Py_DECREF(cls);
        return result;
    }

    cp = PyObject_GetAttrString(cls, "__provides__");
    if (cp == NULL)
    {
        /* The the class has no provides, assume we're done: */
        PyErr_Clear();

        Py_DECREF(cls);
        return result;
    }

    if (cp == result)
    {
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


/*
 *  Module-scope functions
 */
static struct PyMethodDef m_methods[] = {
    {"implementedBy",
        (PyCFunction)implementedBy, METH_O,
        "Interfaces implemented by a class or factory.\n"
        "Raises TypeError if argument is neither a class nor a callable."},
    {"getObjectSpecification",
        (PyCFunction)getObjectSpecification, METH_O,
        "Get an object's interfaces (internal api)"},
    {"providedBy",
        (PyCFunction)providedBy, METH_O,
        "Get an object's interfaces"},
    {NULL, (PyCFunction)NULL, 0, NULL}            /* sentinel */
};

/* Handler for the 'execute' phase of multi-phase initialization
 *
 * See: https://docs.python.org/3/c-api/module.html#multi-phase-initialization
 * and: https://peps.python.org/pep-0489/#module-execution-phase
 */
static int
exec_module(PyObject* module)
{
    PyObject *adapter_hooks;  /* can't use a static! */
    PyObject *sb;
    PyObject *osd;
    PyObject *cpb;
    PyObject *ib;
    PyObject *lb;
    PyObject *vb;

    _zic_state_init(module);

    adapter_hooks = PyList_New(0);
    if (adapter_hooks == NULL) { return -1; }

    if (PyModule_AddObjectRef(module, "adapter_hooks", adapter_hooks) < 0)
    {
        return -1;
    }

    /* Add types: */
    sb = PyType_FromModuleAndSpec(module, &SpecBase_type_spec, NULL);
    if (sb == NULL) { return -1; }
    if (PyModule_AddObjectRef(module, "SpecificationBase", sb) < 0)
    {
        return -1;
    }

    osd = PyType_FromModuleAndSpec(
        module, &ObjSpecDescr_type_spec, NULL);
    if (osd == NULL) { return -1; }
    if (PyModule_AddObject(module, "ObjectSpecificationDescriptor", osd) < 0)
    {
        return -1;
    }

    cpb = PyType_FromModuleAndSpec(module, &ClsPrvBase_type_spec, sb);
    if (cpb == NULL) { return -1; }
    if (PyModule_AddObject(module, "ClassProvidesBase", cpb) < 0)
    {
        return -1;
    }

    ib = PyType_FromModuleAndSpec(module, &InterfaceBaseSpec, sb);
    if (ib == NULL) { return -1; }
    if (PyModule_AddObject(module, "InterfaceBase", ib) < 0)
    {
        return -1;
    }

    lb = PyType_FromModuleAndSpec(module, &LkpBase_type_spec, NULL);
    if (lb == NULL) { return -1; }
    if (PyModule_AddObject(module, "LookupBase", lb) < 0)
    {
        return -1;
    }

    vb = PyType_FromModuleAndSpec(module, &VfyBase_type_spec, lb);
    if (vb == NULL) { return -1; }
    if (PyModule_AddObject(module, "VerifyingBase", vb) < 0)
    {
        return -1;
    }

    return 0;
};

static char module_doc[] = "C optimizations for zope.interface\n\n";

/* Slot definitions for multi-phase initialization
 *
 * See: https://docs.python.org/3/c-api/module.html#multi-phase-initialization
 * and: https://peps.python.org/pep-0489
 */
static PyModuleDef_Slot m_slots[] = {
    {Py_mod_exec,       exec_module},
    {0,                 NULL}
};

static struct PyModuleDef _zic_module = {
    PyModuleDef_HEAD_INIT,
    .m_name="_zope_interface_coptimizations",
    .m_doc=module_doc,
    .m_methods=m_methods,
    .m_slots=m_slots,
    .m_size=sizeof(_zic_state_rec),
    .m_traverse=_zic_state_traverse,
    .m_clear=_zic_state_clear,
};

#undef LOG
#define LOG(msg)
//#define LOG(msg) printf((msg))
static PyObject*
_get_module(PyTypeObject *typeobj)
{
    if (PyType_Check(typeobj)) {
        LOG("_get_module: valid typeobj argument\n");
        return PyType_GetModuleByDef((PyTypeObject*)typeobj, &_zic_module);
    }
    LOG("_get_module: invalid typeobj argument\n");
    PyErr_SetString(PyExc_TypeError, "_get_module: called w/ non-type");
    return NULL;
}

static PyObject *
init(void)
{
    PyObject *m;

#define DEFINE_STRING(S) \
  if(! (str ## S = PyUnicode_FromString(# S))) return NULL

    DEFINE_STRING(_call_conform);
    DEFINE_STRING(_uncached_lookup);
    DEFINE_STRING(_uncached_lookupAll);
    DEFINE_STRING(_uncached_subscriptions);

    DEFINE_STRING(changed);
    DEFINE_STRING(__adapt__);
#undef DEFINE_STRING

    m = PyModuleDef_Init(&_zic_module);
    if (m == NULL) { return NULL; }

    return m;
}

PyMODINIT_FUNC
PyInit__zope_interface_coptimizations(void)
{
    return init();
}

#ifdef __clang__
#pragma clang diagnostic pop
#endif
