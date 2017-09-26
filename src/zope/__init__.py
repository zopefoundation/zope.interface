# this is a namespace package
try:
    from pkg_resources import declare_namespace
    declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)
