"""Unit tests for ServiceManager."""

import unittest

from pyrox.services.service import ServiceManager


# ---------------------------------------------------------------------------
# Stub helpers
# ---------------------------------------------------------------------------

class _PlainService:
    """A plain service with no special protocols."""
    pass


class _StatusService:
    """A service that satisfies ISupportsServiceStatus via duck-typing."""

    def __init__(self, active: bool = True, initialized: bool = True):
        self._active = active
        self._initialized = initialized

    def is_service_active(self) -> bool:
        return self._active

    def is_service_initialized(self) -> bool:
        return self._initialized


class _ViewableService:
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

class TestServiceManagerInstantiation(unittest.TestCase):
    """ServiceManager must be a static-only class."""

    def test_cannot_be_instantiated(self):
        """Attempting to instantiate ServiceManager raises RuntimeError."""
        with self.assertRaises(RuntimeError) as ctx:
            ServiceManager()
        self.assertIn("static class", str(ctx.exception))


class TestServiceManagerRegister(unittest.TestCase):
    """Tests for register_service."""

    def setUp(self):
        ServiceManager.clear()

    def tearDown(self):
        ServiceManager.clear()

    def test_register_returns_true_on_success(self):
        """Registering a new service returns True."""
        svc = _PlainService()
        result = ServiceManager.register_service("svc", svc)
        self.assertTrue(result)

    def test_register_duplicate_name_returns_false(self):
        """Registering under an already-used name returns False."""
        svc = _PlainService()
        ServiceManager.register_service("svc", svc)
        result = ServiceManager.register_service("svc", _PlainService())
        self.assertFalse(result)

    def test_register_duplicate_does_not_replace(self):
        """The original service is not replaced when a duplicate is rejected."""
        original = _PlainService()
        intruder = _PlainService()
        ServiceManager.register_service("svc", original)
        ServiceManager.register_service("svc", intruder)
        self.assertIs(ServiceManager.get_service("svc"), original)

    def test_register_multiple_distinct_names(self):
        """Multiple services with different names can all be registered."""
        svc_a = _PlainService()
        svc_b = _PlainService()
        self.assertTrue(ServiceManager.register_service("a", svc_a))
        self.assertTrue(ServiceManager.register_service("b", svc_b))
        self.assertEqual(ServiceManager.service_count(), 2)

    def test_register_none_service_is_allowed(self):
        """A None value may be registered (no type restriction imposed)."""
        result = ServiceManager.register_service("null_svc", None)
        self.assertTrue(result)
        self.assertIsNone(ServiceManager.get_service("null_svc"))


class TestServiceManagerUnregister(unittest.TestCase):
    """Tests for unregister_service."""

    def setUp(self):
        ServiceManager.clear()

    def tearDown(self):
        ServiceManager.clear()

    def test_unregister_existing_returns_true(self):
        """Unregistering a known service returns True."""
        ServiceManager.register_service("svc", _PlainService())
        self.assertTrue(ServiceManager.unregister_service("svc"))

    def test_unregister_existing_removes_service(self):
        """After unregistering, the service is no longer retrievable."""
        ServiceManager.register_service("svc", _PlainService())
        ServiceManager.unregister_service("svc")
        self.assertIsNone(ServiceManager.get_service("svc"))

    def test_unregister_nonexistent_returns_false(self):
        """Unregistering a name that was never registered returns False."""
        self.assertFalse(ServiceManager.unregister_service("ghost"))

    def test_unregister_reduces_count(self):
        """Unregistering a service decrements the service count."""
        ServiceManager.register_service("s1", _PlainService())
        ServiceManager.register_service("s2", _PlainService())
        ServiceManager.unregister_service("s1")
        self.assertEqual(ServiceManager.service_count(), 1)

    def test_reregister_after_unregister(self):
        """A name can be re-registered after being unregistered."""
        svc_v2 = _PlainService()
        ServiceManager.register_service("svc", _PlainService())
        ServiceManager.unregister_service("svc")
        ServiceManager.register_service("svc", svc_v2)
        self.assertIs(ServiceManager.get_service("svc"), svc_v2)


class TestServiceManagerHasService(unittest.TestCase):
    """Tests for has_service."""

    def setUp(self):
        ServiceManager.clear()

    def tearDown(self):
        ServiceManager.clear()

    def test_has_service_true_when_registered(self):
        ServiceManager.register_service("svc", _PlainService())
        self.assertTrue(ServiceManager.has_service("svc"))

    def test_has_service_false_when_not_registered(self):
        self.assertFalse(ServiceManager.has_service("missing"))

    def test_has_service_false_after_unregister(self):
        ServiceManager.register_service("svc", _PlainService())
        ServiceManager.unregister_service("svc")
        self.assertFalse(ServiceManager.has_service("svc"))


class TestServiceManagerGetService(unittest.TestCase):
    """Tests for get_service."""

    def setUp(self):
        ServiceManager.clear()

    def tearDown(self):
        ServiceManager.clear()

    def test_get_service_returns_correct_instance(self):
        svc = _PlainService()
        ServiceManager.register_service("svc", svc)
        self.assertIs(ServiceManager.get_service("svc"), svc)

    def test_get_service_returns_none_for_unknown_name(self):
        self.assertIsNone(ServiceManager.get_service("unknown"))


class TestServiceManagerGetServiceOfType(unittest.TestCase):
    """Tests for get_service_of_type."""

    def setUp(self):
        ServiceManager.clear()

    def tearDown(self):
        ServiceManager.clear()

    def test_returns_matching_services(self):
        svc_a = _StatusService()
        svc_b = _PlainService()
        ServiceManager.register_service("status", svc_a)
        ServiceManager.register_service("plain", svc_b)
        results = ServiceManager.get_service_of_type(_StatusService)
        self.assertIn(svc_a, results)
        self.assertNotIn(svc_b, results)

    def test_returns_empty_list_when_no_match(self):
        ServiceManager.register_service("plain", _PlainService())
        self.assertEqual(ServiceManager.get_service_of_type(_StatusService), [])

    def test_returns_empty_list_when_no_services(self):
        self.assertEqual(ServiceManager.get_service_of_type(_PlainService), [])

    def test_returns_subclass_instances(self):
        """get_service_of_type should match subclasses of the requested type."""
        full = _FullService()
        ServiceManager.register_service("full", full)
        results = ServiceManager.get_service_of_type(_StatusService)
        self.assertIn(full, results)

    def test_returns_multiple_matching_services(self):
        svc_a = _StatusService()
        svc_b = _StatusService(active=False)
        ServiceManager.register_service("a", svc_a)
        ServiceManager.register_service("b", svc_b)
        results = ServiceManager.get_service_of_type(_StatusService)
        self.assertEqual(len(results), 2)


class TestServiceManagerGetAllServices(unittest.TestCase):
    """Tests for get_all_services."""

    def setUp(self):
        ServiceManager.clear()

    def tearDown(self):
        ServiceManager.clear()

    def test_returns_empty_dict_when_empty(self):
        self.assertEqual(ServiceManager.get_all_services(), {})

    def test_returns_all_registered_services(self):
        svc_a = _PlainService()
        svc_b = _PlainService()
        ServiceManager.register_service("a", svc_a)
        ServiceManager.register_service("b", svc_b)
        result = ServiceManager.get_all_services()
        self.assertEqual(result, {"a": svc_a, "b": svc_b})

    def test_returns_a_copy_not_the_internal_dict(self):
        """Modifying the returned dict must not affect the manager state."""
        ServiceManager.register_service("svc", _PlainService())
        snapshot = ServiceManager.get_all_services()
        snapshot["injected"] = _PlainService()
        self.assertFalse(ServiceManager.has_service("injected"))


class TestServiceManagerListServiceNames(unittest.TestCase):
    """Tests for list_service_names."""

    def setUp(self):
        ServiceManager.clear()

    def tearDown(self):
        ServiceManager.clear()

    def test_empty_when_no_services(self):
        self.assertEqual(ServiceManager.list_service_names(), [])

    def test_contains_registered_names(self):
        ServiceManager.register_service("alpha", _PlainService())
        ServiceManager.register_service("beta", _PlainService())
        names = ServiceManager.list_service_names()
        self.assertIn("alpha", names)
        self.assertIn("beta", names)

    def test_does_not_contain_unregistered_name(self):
        ServiceManager.register_service("alpha", _PlainService())
        ServiceManager.unregister_service("alpha")
        self.assertNotIn("alpha", ServiceManager.list_service_names())


class TestServiceManagerServiceCount(unittest.TestCase):
    """Tests for service_count."""

    def setUp(self):
        ServiceManager.clear()

    def tearDown(self):
        ServiceManager.clear()

    def test_zero_when_empty(self):
        self.assertEqual(ServiceManager.service_count(), 0)

    def test_increments_on_register(self):
        ServiceManager.register_service("s1", _PlainService())
        self.assertEqual(ServiceManager.service_count(), 1)
        ServiceManager.register_service("s2", _PlainService())
        self.assertEqual(ServiceManager.service_count(), 2)

    def test_decrements_on_unregister(self):
        ServiceManager.register_service("s1", _PlainService())
        ServiceManager.register_service("s2", _PlainService())
        ServiceManager.unregister_service("s1")
        self.assertEqual(ServiceManager.service_count(), 1)

    def test_unchanged_after_failed_registration(self):
        ServiceManager.register_service("s1", _PlainService())
        ServiceManager.register_service("s1", _PlainService())  # duplicate
        self.assertEqual(ServiceManager.service_count(), 1)


class TestServiceManagerClear(unittest.TestCase):
    """Tests for clear."""

    def tearDown(self):
        ServiceManager.clear()

    def test_clear_removes_all_services(self):
        ServiceManager.register_service("a", _PlainService())
        ServiceManager.register_service("b", _PlainService())
        ServiceManager.clear()
        self.assertEqual(ServiceManager.service_count(), 0)

    def test_clear_on_empty_manager_is_safe(self):
        ServiceManager.clear()
        ServiceManager.clear()  # Should not raise
        self.assertEqual(ServiceManager.service_count(), 0)

    def test_register_after_clear_works(self):
        ServiceManager.register_service("svc", _PlainService())
        ServiceManager.clear()
        svc_new = _PlainService()
        result = ServiceManager.register_service("svc", svc_new)
        self.assertTrue(result)
        self.assertIs(ServiceManager.get_service("svc"), svc_new)


class TestServiceManagerServicesWithStatus(unittest.TestCase):
    """Tests for get_services_with_status."""

    def setUp(self):
        ServiceManager.clear()

    def tearDown(self):
        ServiceManager.clear()

    def test_returns_only_status_services(self):
        status_svc = _StatusService()
        plain_svc = _PlainService()
        ServiceManager.register_service("status", status_svc)
        ServiceManager.register_service("plain", plain_svc)
        result = ServiceManager.get_services_with_status()
        names = [list(d.keys())[0] for d in result]
        self.assertIn("status", names)
        self.assertNotIn("plain", names)

    def test_correct_instance_in_result(self):
        svc = _StatusService()
        ServiceManager.register_service("status", svc)
        result = ServiceManager.get_services_with_status()
        self.assertIs(result[0]["status"], svc)

    def test_empty_when_no_status_services(self):
        ServiceManager.register_service("plain", _PlainService())
        self.assertEqual(ServiceManager.get_services_with_status(), [])

    def test_empty_when_no_services(self):
        self.assertEqual(ServiceManager.get_services_with_status(), [])

    def test_full_service_included(self):
        """A service implementing both protocols is included in status results."""
        full = _FullService()
        ServiceManager.register_service("full", full)
        result = ServiceManager.get_services_with_status()
        self.assertEqual(len(result), 1)


class TestServiceManagerServicesWithViewableAttributes(unittest.TestCase):
    """Tests for get_services_with_viewable_attributes."""

    def setUp(self):
        ServiceManager.clear()

    def tearDown(self):
        ServiceManager.clear()

    def test_returns_only_viewable_services(self):
        viewable = _ViewableService()
        plain = _PlainService()
        ServiceManager.register_service("viewable", viewable)
        ServiceManager.register_service("plain", plain)
        result = ServiceManager.get_services_with_viewable_attributes()
        names = [list(d.keys())[0] for d in result]
        self.assertIn("viewable", names)
        self.assertNotIn("plain", names)

    def test_correct_instance_in_result(self):
        svc = _ViewableService({"x": 42})
        ServiceManager.register_service("viewable", svc)
        result = ServiceManager.get_services_with_viewable_attributes()
        instance = result[0]["viewable"]
        self.assertIs(instance, svc)
        self.assertEqual(instance.get_viewable_attributes(), {"x": 42})

    def test_empty_when_no_viewable_services(self):
        ServiceManager.register_service("plain", _PlainService())
        self.assertEqual(ServiceManager.get_services_with_viewable_attributes(), [])

    def test_empty_when_no_services(self):
        self.assertEqual(ServiceManager.get_services_with_viewable_attributes(), [])

    def test_full_service_included(self):
        """A service implementing both protocols is included in viewable results."""
        full = _FullService()
        ServiceManager.register_service("full", full)
        result = ServiceManager.get_services_with_viewable_attributes()
        self.assertEqual(len(result), 1)


class TestServiceManagerIntegration(unittest.TestCase):
    """Integration-style tests combining multiple operations."""

    def setUp(self):
        ServiceManager.clear()

    def tearDown(self):
        ServiceManager.clear()

    def test_register_retrieve_unregister_cycle(self):
        """Full lifecycle: register → retrieve → unregister → confirm gone."""
        svc = _PlainService()
        ServiceManager.register_service("lifecycle", svc)
        self.assertIs(ServiceManager.get_service("lifecycle"), svc)
        ServiceManager.unregister_service("lifecycle")
        self.assertIsNone(ServiceManager.get_service("lifecycle"))

    def test_mixed_services_filter_independently(self):
        """Status and viewable filters each return only their matching subset."""
        ServiceManager.register_service("plain", _PlainService())
        ServiceManager.register_service("status_only", _StatusService())
        ServiceManager.register_service("viewable_only", _ViewableService())
        ServiceManager.register_service("full", _FullService())

        status_names = {list(d.keys())[0] for d in ServiceManager.get_services_with_status()}
        viewable_names = {list(d.keys())[0] for d in ServiceManager.get_services_with_viewable_attributes()}

        self.assertEqual(status_names, {"status_only", "full"})
        self.assertEqual(viewable_names, {"viewable_only", "full"})

    def test_service_count_consistent_across_operations(self):
        """service_count stays in sync through mixed register/unregister operations."""
        self.assertEqual(ServiceManager.service_count(), 0)
        ServiceManager.register_service("a", _PlainService())
        ServiceManager.register_service("b", _PlainService())
        ServiceManager.register_service("a", _PlainService())  # duplicate – ignored
        self.assertEqual(ServiceManager.service_count(), 2)
        ServiceManager.unregister_service("b")
        self.assertEqual(ServiceManager.service_count(), 1)
        ServiceManager.clear()
        self.assertEqual(ServiceManager.service_count(), 0)


if __name__ == "__main__":
    unittest.main()
