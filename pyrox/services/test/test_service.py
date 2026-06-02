"""Unit tests for ServiceManager."""
import pytest

from pyrox.services.service import ServiceManager
from pyrox.interfaces import IHasViewableServiceAttributes, ISupportsServiceStatus


# ---------------------------------------------------------------------------
# Stub helpers
# ---------------------------------------------------------------------------

class _PlainService:
    """A plain service with no special protocols."""


class _StatusService(ISupportsServiceStatus):
    """A service that satisfies ISupportsServiceStatus via duck-typing."""

    def __init__(self, active: bool = True, initialized: bool = True):
        self._active = active
        self._initialized = initialized

    def is_service_active(self) -> bool:
        return self._active

    def is_service_initialized(self) -> bool:
        return self._initialized


class _ViewableService(IHasViewableServiceAttributes):
    """A service that satisfies IHasViewableServiceAttributes via duck-typing."""

    def __init__(self, attrs: dict | None = None):
        self._attrs = attrs or {"key": "value"}

    def get_viewable_attributes(self) -> dict:
        return self._attrs


class _FullService(_StatusService, _ViewableService):
    """A service implementing both status and viewable-attributes protocols."""

    def __init__(self):
        _StatusService.__init__(self)
        _ViewableService.__init__(self, {"a": 1, "b": 2})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestServiceManagerInstantiation:
    """ServiceManager must be a static-only class."""

    def test_cannot_be_instantiated(self):
        """Attempting to instantiate ServiceManager raises RuntimeError."""
        with pytest.raises(RuntimeError, match="static class"):
            ServiceManager()
            assert False, "Expected RuntimeError was not raised"
        assert True


class TestServiceManagerRegister:
    """Tests for register_service."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_register_returns_true_on_success(self):
        """Registering a new service returns True."""
        svc = _PlainService()
        result = ServiceManager.register_service("svc", svc)
        assert result is True, "Expected register_service to return True for new service"

    def test_register_duplicate_name_returns_false(self):
        """Registering under an already-used name returns False."""
        svc = _PlainService()
        ServiceManager.register_service("svc", svc)
        result = ServiceManager.register_service("svc", _PlainService())
        assert result is False, "Expected register_service to return False for duplicate name"

    def test_register_duplicate_does_not_replace(self):
        """The original service is not replaced when a duplicate is rejected."""
        original = _PlainService()
        intruder = _PlainService()
        ServiceManager.register_service("svc", original)
        ServiceManager.register_service("svc", intruder)
        assert ServiceManager.get_service("svc") is original, "Original service should not be replaced by duplicate registration"

    def test_register_multiple_distinct_names(self):
        """Multiple services with different names can all be registered."""
        svc_a = _PlainService()
        svc_b = _PlainService()
        assert ServiceManager.register_service("a", svc_a) is True, "Expected first registration to succeed"
        assert ServiceManager.register_service("b", svc_b) is True, "Expected second registration to succeed"
        assert ServiceManager.service_count() == 2, "Expected service count to be 2 after registering two distinct services"

    def test_register_none_service_is_allowed(self):
        """A None value may be registered (no type restriction imposed)."""
        result = ServiceManager.register_service("null_svc", None)
        assert result is True, "Expected register_service to allow None as a service instance"
        assert ServiceManager.has_service("null_svc") is True, "Expected has_service to return True for registered None service"


class TestServiceManagerUnregister:
    """Tests for unregister_service."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_unregister_existing_returns_true(self):
        """Unregistering a known service returns True."""
        ServiceManager.register_service("svc", _PlainService())
        assert ServiceManager.unregister_service("svc") is True, "Expected unregister_service to return True for existing service"

    def test_unregister_existing_removes_service(self):
        """After unregistering, the service is no longer retrievable."""
        ServiceManager.register_service("svc", _PlainService())
        ServiceManager.unregister_service("svc")
        assert ServiceManager.get_service("svc") is None, "Expected get_service to return None after service has been unregistered"

    def test_unregister_nonexistent_returns_false(self):
        """Unregistering a name that was never registered returns False."""
        assert ServiceManager.unregister_service("ghost") is False, "Expected unregister_service to return False for non-existent service"

    def test_unregister_reduces_count(self):
        """Unregistering a service decrements the service count."""
        ServiceManager.register_service("s1", _PlainService())
        ServiceManager.register_service("s2", _PlainService())
        ServiceManager.unregister_service("s1")
        assert ServiceManager.service_count() == 1, "Expected service count to be 1 after unregistering one of two services"

    def test_reregister_after_unregister(self):
        """A name can be re-registered after being unregistered."""
        svc_v2 = _PlainService()
        ServiceManager.register_service("svc", _PlainService())
        ServiceManager.unregister_service("svc")
        ServiceManager.register_service("svc", svc_v2)
        assert ServiceManager.has_service("svc") is True, "Expected has_service to return True for re-registered service"


class TestServiceManagerHasService:
    """Tests for has_service."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_has_service_true_when_registered(self):
        ServiceManager.register_service("svc", _PlainService())
        assert ServiceManager.has_service("svc") is True, "Expected has_service to return True for registered service"

    def test_has_service_false_when_not_registered(self):
        assert ServiceManager.has_service("missing") is False, "Expected has_service to return False for unregistered service name"

    def test_has_service_false_after_unregister(self):
        ServiceManager.register_service("svc", _PlainService())
        ServiceManager.unregister_service("svc")
        assert ServiceManager.has_service("svc") is False, "Expected has_service to return False after service has been unregistered"


class TestServiceManagerGetService:
    """Tests for get_service."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_get_service_returns_correct_instance(self):
        svc = _PlainService()
        ServiceManager.register_service("svc", svc)
        assert ServiceManager.get_service("svc") is svc, "Expected get_service to return the exact instance that was registered"

    def test_get_service_returns_none_for_unknown_name(self):
        assert ServiceManager.get_service("unknown") is None, "Expected get_service to return None for unregistered service name"


class TestServiceManagerGetServiceOfType:
    """Tests for get_service_of_type."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_returns_matching_services(self):
        svc_a = _StatusService()
        svc_b = _PlainService()
        ServiceManager.register_service("status", svc_a)
        ServiceManager.register_service("plain", svc_b)
        results = ServiceManager.get_service_of_type(_StatusService)
        assert len(results) == 1, "Expected exactly one service of type _StatusService"
        assert results[0] is svc_a, "Expected the returned service to be the one registered as _StatusService"
        assert svc_b not in results, "Expected _PlainService instance not to be included in results for _StatusService type"

    def test_returns_empty_list_when_no_match(self):
        ServiceManager.register_service("plain", _PlainService())
        assert ServiceManager.get_service_of_type(
            _StatusService) == [], "Expected get_service_of_type to return empty list when no services match the requested type"

    def test_returns_empty_list_when_no_services(self):
        assert ServiceManager.get_service_of_type(
            _StatusService) == [], "Expected get_service_of_type to return empty list when no services are registered"

    def test_returns_subclass_instances(self):
        """get_service_of_type should match subclasses of the requested type."""
        full = _FullService()
        ServiceManager.register_service("full", full)
        results = ServiceManager.get_service_of_type(_StatusService)
        assert len(results) == 1, "Expected exactly one service of type _StatusService (including subclasses)"

    def test_returns_multiple_matching_services(self):
        svc_a = _StatusService()
        svc_b = _StatusService(active=False)
        ServiceManager.register_service("a", svc_a)
        ServiceManager.register_service("b", svc_b)
        results = ServiceManager.get_service_of_type(_StatusService)
        assert len(results) == 2, "Expected both registered _StatusService instances to be returned"


class TestServiceManagerGetAllServices:
    """Tests for get_all_services."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_returns_empty_dict_when_empty(self):
        assert not ServiceManager.get_all_services(), "Expected get_all_services to return empty dict when no services are registered"

    def test_returns_all_registered_services(self):
        svc_a = _PlainService()
        svc_b = _PlainService()
        ServiceManager.register_service("a", svc_a)
        ServiceManager.register_service("b", svc_b)
        result = ServiceManager.get_all_services()
        assert len(result) == 2, "Expected get_all_services to return dict with two entries"
        assert result["a"] is svc_a, "Expected service 'a' in result to be the instance registered as 'a'"
        assert result["b"] is svc_b, "Expected service 'b' in result to be the instance registered as 'b'"

    def test_returns_a_copy_not_the_internal_dict(self):
        """Modifying the returned dict must not affect the manager state."""
        ServiceManager.register_service("svc", _PlainService())
        snapshot = ServiceManager.get_all_services()
        snapshot["injected"] = _PlainService()
        assert not ServiceManager.has_service(
            "injected"), "Modifying the dict returned by get_all_services should not affect the registered services in the manager"


class TestServiceManagerListServiceNames:
    """Tests for list_service_names."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_empty_when_no_services(self):
        assert not ServiceManager.list_service_names(), "Expected list_service_names to return empty list when no services are registered"

    def test_contains_registered_names(self):
        ServiceManager.register_service("alpha", _PlainService())
        ServiceManager.register_service("beta", _PlainService())
        names = ServiceManager.list_service_names()
        assert len(names) == 2, "Expected list_service_names to return list with two entries"
        assert "alpha" in names, "Expected 'alpha' to be in the list of service names"
        assert "beta" in names, "Expected 'beta' to be in the list of service names"

    def test_does_not_contain_unregistered_name(self):
        ServiceManager.register_service("alpha", _PlainService())
        ServiceManager.unregister_service("alpha")
        assert "alpha" not in ServiceManager.list_service_names(), \
            "Expected list_service_names not to include 'alpha' after it has been unregistered"


class TestServiceManagerServiceCount:
    """Tests for service_count."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_zero_when_empty(self):
        assert ServiceManager.service_count() == 0, "Expected service_count to be 0 when no services are registered"

    def test_increments_on_register(self):
        ServiceManager.register_service("s1", _PlainService())
        assert ServiceManager.service_count() == 1, "Expected service_count to be 1 after registering one service"
        ServiceManager.register_service("s2", _PlainService())
        assert ServiceManager.service_count() == 2, "Expected service_count to be 2 after registering two services"

    def test_decrements_on_unregister(self):
        ServiceManager.register_service("s1", _PlainService())
        ServiceManager.register_service("s2", _PlainService())
        ServiceManager.unregister_service("s1")
        assert ServiceManager.service_count() == 1, "Expected service_count to be 1 after unregistering one of two services"

    def test_unchanged_after_failed_registration(self):
        ServiceManager.register_service("s1", _PlainService())
        ServiceManager.register_service("s1", _PlainService())  # duplicate
        assert ServiceManager.service_count() == 1, "Expected service_count to remain 1 after failed duplicate registration"


class TestServiceManagerClear:
    """Tests for clear."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_clear_removes_all_services(self):
        ServiceManager.register_service("a", _PlainService())
        ServiceManager.register_service("b", _PlainService())
        ServiceManager.clear()
        assert not ServiceManager.get_all_services(), "Expected get_all_services to return empty dict after clear"

    def test_clear_on_empty_manager_is_safe(self):
        ServiceManager.clear()
        ServiceManager.clear()
        assert not ServiceManager.get_all_services(), "Expected get_all_services to return empty dict after clear on already-empty manager"

    def test_register_after_clear_works(self):
        ServiceManager.register_service("svc", _PlainService())
        ServiceManager.clear()
        svc_new = _PlainService()
        result = ServiceManager.register_service("svc", svc_new)
        assert result is True, "Expected register_service to succeed after clear"
        assert ServiceManager.has_service("svc") is True, "Expected has_service to return True for service registered after clear"


class TestServiceManagerServicesWithStatus:
    """Tests for get_services_with_status."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_returns_only_status_services(self):
        status_svc = _StatusService()
        plain_svc = _PlainService()
        ServiceManager.register_service("status", status_svc)
        ServiceManager.register_service("plain", plain_svc)
        result = ServiceManager.get_services_with_status()
        names = [list(d.keys())[0] for d in result]
        assert len(result) == 1, "Expected exactly one service with status in the result"
        assert 'status' in names, "Expected 'status' service to be included in the result"
        assert 'plain' not in names, "Expected 'plain' service not to be included in the result since it does not support status"

    def test_correct_instance_in_result(self):
        svc = _StatusService()
        ServiceManager.register_service("status", svc)
        result = ServiceManager.get_services_with_status()
        assert len(result) == 1, "Expected exactly one service with status in the result"
        assert list(result[0].keys())[0] == "status", "Expected the service name in the result to be 'status'"

    def test_empty_when_no_status_services(self):
        ServiceManager.register_service("plain", _PlainService())
        assert not ServiceManager.get_services_with_status(), \
            "Expected get_services_with_status to return empty list when no services support status"

    def test_empty_when_no_services(self):
        assert not ServiceManager.get_services_with_status(), \
            "Expected get_services_with_status to return empty list when no services are registered"

    def test_full_service_included(self):
        """A service implementing both protocols is included in status results."""
        full = _FullService()
        ServiceManager.register_service("full", full)
        result = ServiceManager.get_services_with_status()
        assert len(result) == 1, "Expected exactly one service with status in the result"


class TestServiceManagerServicesWithViewableAttributes:
    """Tests for get_services_with_viewable_attributes."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_returns_only_viewable_services(self):
        viewable = _ViewableService()
        plain = _PlainService()
        ServiceManager.register_service("viewable", viewable)
        ServiceManager.register_service("plain", plain)
        result = ServiceManager.get_services_with_viewable_attributes()
        names = [list(d.keys())[0] for d in result]
        assert len(result) == 1, "Expected exactly one service with viewable attributes in the result"
        assert "viewable" in names, "Expected 'viewable' service to be included in the result"
        assert "plain" not in names, "Expected 'plain' service not to be included in the result since it does not have viewable attributes"

    def test_correct_instance_in_result(self):
        svc = _ViewableService({"x": 42})
        ServiceManager.register_service("viewable", svc)
        result = ServiceManager.get_services_with_viewable_attributes()
        instance = result[0]["viewable"]
        assert isinstance(instance, IHasViewableServiceAttributes), "Expected the returned instance to implement IHasViewableServiceAttributes"
        assert instance.get_viewable_attributes(
        ) == {"x": 42}, "Expected get_viewable_attributes to return the correct attributes for the service"

    def test_empty_when_no_viewable_services(self):
        ServiceManager.register_service("plain", _PlainService())
        assert not ServiceManager.get_services_with_viewable_attributes(
        ), "Expected get_services_with_viewable_attributes to return empty list when no services have viewable attributes"

    def test_empty_when_no_services(self):
        assert not ServiceManager.get_services_with_viewable_attributes(
        ), "Expected get_services_with_viewable_attributes to return empty list when no services are registered"

    def test_full_service_included(self):
        """A service implementing both protocols is included in viewable results."""
        full = _FullService()
        ServiceManager.register_service("full", full)
        result = ServiceManager.get_services_with_viewable_attributes()
        assert len(result) == 1, "Expected exactly one service with viewable attributes in the result"


class TestServiceManagerIntegration:
    """Integration-style tests combining multiple operations."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear the ServiceManager before and after each test."""
        ServiceManager.clear()
        yield
        ServiceManager.clear()

    def test_register_retrieve_unregister_cycle(self):
        """Full lifecycle: register → retrieve → unregister → confirm gone."""
        svc = _PlainService()
        ServiceManager.register_service("lifecycle", svc)
        assert ServiceManager.has_service("lifecycle") is True, "Expected has_service to return True after registering service"
        ServiceManager.unregister_service("lifecycle")
        assert ServiceManager.has_service("lifecycle") is False, "Expected has_service to return False after unregistering service"

    def test_mixed_services_filter_independently(self):
        """Status and viewable filters each return only their matching subset."""
        ServiceManager.register_service("plain", _PlainService())
        ServiceManager.register_service("status_only", _StatusService())
        ServiceManager.register_service("viewable_only", _ViewableService())
        ServiceManager.register_service("full", _FullService())

        status_names = {list(d.keys())[0] for d in ServiceManager.get_services_with_status()}
        viewable_names = {list(d.keys())[0] for d in ServiceManager.get_services_with_viewable_attributes()}

        assert len(status_names) == 2, "Expected two services to be returned by get_services_with_status"
        assert len(viewable_names) == 2, "Expected two services to be returned by get_services_with_viewable_attributes"
        assert "status_only" in status_names, "Expected 'status_only' service to be included in status results"
        assert "viewable_only" in viewable_names, "Expected 'viewable_only' service to be included in viewable results"
        assert "full" in status_names and "full" in viewable_names, "Expected 'full' service to be included in both status and viewable results"

    def test_service_count_consistent_across_operations(self):
        """service_count stays in sync through mixed register/unregister operations."""
        assert not ServiceManager.service_count(), "Expected service_count to be 0 at start of test"
        ServiceManager.register_service("a", _PlainService())
        ServiceManager.register_service("b", _PlainService())
        ServiceManager.register_service("a", _PlainService())  # duplicate – ignored
        assert ServiceManager.service_count() == 2, "Expected service_count to be 2 after registering two distinct services and one duplicate"
        ServiceManager.unregister_service("b")
        assert ServiceManager.service_count() == 1, "Expected service_count to be 1 after unregistering one of two services"
        ServiceManager.clear()
        assert ServiceManager.service_count() == 0, "Expected service_count to be 0 after clear"


if __name__ == "__main__":
    pytest.main([__file__])
