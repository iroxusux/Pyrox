"""Unit tests for ServiceManager."""
import pytest

from pyrox.services.service import ServiceManager
from pyrox.interfaces import IStatusServiceMixin


# ---------------------------------------------------------------------------
# Stub helpers
# ---------------------------------------------------------------------------

class _FullService(IStatusServiceMixin):
    """A service implementing both status and viewable-attributes protocols."""

    def __init__(self):
        super().__init__()
        self._viewable_attributes = {"full": True}

    def get_viewable_attributes(self):
        return self._viewable_attributes

    def get_status(self):
        return {"status": "full"}

    def is_service_active(self) -> bool:
        return True

    def is_service_initialized(self) -> bool:
        return True


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
        svc = _FullService()
        result = ServiceManager.register_service("svc", svc)
        assert result is True, "Expected register_service to return True for new service"

    def test_register_duplicate_name_returns_false(self):
        """Registering under an already-used name returns False."""
        svc = _FullService()
        ServiceManager.register_service("svc", svc)
        result = ServiceManager.register_service("svc", _FullService())
        assert result is False, "Expected register_service to return False for duplicate name"

    def test_register_duplicate_does_not_replace(self):
        """The original service is not replaced when a duplicate is rejected."""
        original = _FullService()
        intruder = _FullService()
        ServiceManager.register_service("svc", original)
        ServiceManager.register_service("svc", intruder)
        assert ServiceManager.get_service("svc") is original, "Original service should not be replaced by duplicate registration"

    def test_register_multiple_distinct_names(self):
        """Multiple services with different names can all be registered."""
        svc_a = _FullService()
        svc_b = _FullService()
        assert ServiceManager.register_service("a", svc_a) is True, "Expected first registration to succeed"
        assert ServiceManager.register_service("b", svc_b) is True, "Expected second registration to succeed"
        assert ServiceManager.service_count() == 2, "Expected service count to be 2 after registering two distinct services"

    def test_register_none_service_is_allowed(self):
        """A None value may be registered (no type restriction imposed)."""
        with pytest.raises(ValueError, match="must implement IStatusServiceMixin"):
            ServiceManager.register_service("null_svc", None)  # type: ignore


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
        ServiceManager.register_service("svc", _FullService())
        assert ServiceManager.unregister_service("svc") is True, "Expected unregister_service to return True for existing service"

    def test_unregister_existing_removes_service(self):
        """After unregistering, the service is no longer retrievable."""
        ServiceManager.register_service("svc", _FullService())
        ServiceManager.unregister_service("svc")
        assert ServiceManager.get_service("svc") is None, "Expected get_service to return None after service has been unregistered"

    def test_unregister_nonexistent_returns_false(self):
        """Unregistering a name that was never registered returns False."""
        assert ServiceManager.unregister_service("ghost") is False, "Expected unregister_service to return False for non-existent service"

    def test_unregister_reduces_count(self):
        """Unregistering a service decrements the service count."""
        ServiceManager.register_service("s1", _FullService())
        ServiceManager.register_service("s2", _FullService())
        ServiceManager.unregister_service("s1")
        assert ServiceManager.service_count() == 1, "Expected service count to be 1 after unregistering one of two services"

    def test_reregister_after_unregister(self):
        """A name can be re-registered after being unregistered."""
        svc_v2 = _FullService()
        ServiceManager.register_service("svc", _FullService())
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
        ServiceManager.register_service("svc", _FullService())
        assert ServiceManager.has_service("svc") is True, "Expected has_service to return True for registered service"

    def test_has_service_false_when_not_registered(self):
        assert ServiceManager.has_service("missing") is False, "Expected has_service to return False for unregistered service name"

    def test_has_service_false_after_unregister(self):
        ServiceManager.register_service("svc", _FullService())
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
        svc = _FullService()
        ServiceManager.register_service("svc", svc)
        assert ServiceManager.get_service("svc") is svc, "Expected get_service to return the exact instance that was registered"

    def test_get_service_returns_none_for_unknown_name(self):
        assert ServiceManager.get_service("unknown") is None, "Expected get_service to return None for unregistered service name"


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
        svc_a = _FullService()
        svc_b = _FullService()
        ServiceManager.register_service("a", svc_a)
        ServiceManager.register_service("b", svc_b)
        result = ServiceManager.get_all_services()
        assert len(result) == 2, "Expected get_all_services to return dict with two entries"
        assert result["a"] is svc_a, "Expected service 'a' in result to be the instance registered as 'a'"
        assert result["b"] is svc_b, "Expected service 'b' in result to be the instance registered as 'b'"

    def test_returns_a_copy_not_the_internal_dict(self):
        """Modifying the returned dict must not affect the manager state."""
        ServiceManager.register_service("svc", _FullService())
        snapshot = ServiceManager.get_all_services()
        snapshot["injected"] = _FullService()
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
        ServiceManager.register_service("alpha", _FullService())
        ServiceManager.register_service("beta", _FullService())
        names = ServiceManager.list_service_names()
        assert len(names) == 2, "Expected list_service_names to return list with two entries"
        assert "alpha" in names, "Expected 'alpha' to be in the list of service names"
        assert "beta" in names, "Expected 'beta' to be in the list of service names"

    def test_does_not_contain_unregistered_name(self):
        ServiceManager.register_service("alpha", _FullService())
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
        ServiceManager.register_service("s1", _FullService())
        assert ServiceManager.service_count() == 1, "Expected service_count to be 1 after registering one service"
        ServiceManager.register_service("s2", _FullService())
        assert ServiceManager.service_count() == 2, "Expected service_count to be 2 after registering two services"

    def test_decrements_on_unregister(self):
        ServiceManager.register_service("s1", _FullService())
        ServiceManager.register_service("s2", _FullService())
        ServiceManager.unregister_service("s1")
        assert ServiceManager.service_count() == 1, "Expected service_count to be 1 after unregistering one of two services"

    def test_unchanged_after_failed_registration(self):
        ServiceManager.register_service("s1", _FullService())
        ServiceManager.register_service("s1", _FullService())  # duplicate
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
        ServiceManager.register_service("a", _FullService())
        ServiceManager.register_service("b", _FullService())
        ServiceManager.clear()
        assert not ServiceManager.get_all_services(), "Expected get_all_services to return empty dict after clear"

    def test_clear_on_empty_manager_is_safe(self):
        ServiceManager.clear()
        ServiceManager.clear()
        assert not ServiceManager.get_all_services(), "Expected get_all_services to return empty dict after clear on already-empty manager"

    def test_register_after_clear_works(self):
        ServiceManager.register_service("svc", _FullService())
        ServiceManager.clear()
        svc_new = _FullService()
        result = ServiceManager.register_service("svc", svc_new)
        assert result is True, "Expected register_service to succeed after clear"
        assert ServiceManager.has_service("svc") is True, "Expected has_service to return True for service registered after clear"


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
        svc = _FullService()
        ServiceManager.register_service("lifecycle", svc)
        assert ServiceManager.has_service("lifecycle") is True, "Expected has_service to return True after registering service"
        ServiceManager.unregister_service("lifecycle")
        assert ServiceManager.has_service("lifecycle") is False, "Expected has_service to return False after unregistering service"

    def test_service_count_consistent_across_operations(self):
        """service_count stays in sync through mixed register/unregister operations."""
        assert not ServiceManager.service_count(), "Expected service_count to be 0 at start of test"
        ServiceManager.register_service("a", _FullService())
        ServiceManager.register_service("b", _FullService())
        ServiceManager.register_service("a", _FullService())  # duplicate – ignored
        assert ServiceManager.service_count() == 2, "Expected service_count to be 2 after registering two distinct services and one duplicate"
        ServiceManager.unregister_service("b")
        assert ServiceManager.service_count() == 1, "Expected service_count to be 1 after unregistering one of two services"
        ServiceManager.clear()
        assert ServiceManager.service_count() == 0, "Expected service_count to be 0 after clear"


if __name__ == "__main__":
    pytest.main([__file__])
