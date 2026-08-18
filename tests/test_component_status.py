from utils.component_status import (
    LIFECYCLE_DEPLOYED,
    LIFECYCLE_IN_ASSEMBLY,
    LIFECYCLE_STOCK,
    STATUS_INSTALLED,
    STATUS_RESERVED,
    STATUS_STOCK,
    assignment_component_state,
)


def test_assignment_component_state_prefers_deployment_for_real_assignments():
    status, lifecycle = assignment_component_state(assigned_pc="PC-01")
    assert status == STATUS_INSTALLED
    assert lifecycle == LIFECYCLE_DEPLOYED


def test_assignment_component_state_uses_reservation_when_only_build_order_exists():
    status, lifecycle = assignment_component_state(build_order_id=12)
    assert status == STATUS_RESERVED
    assert lifecycle == LIFECYCLE_IN_ASSEMBLY


def test_assignment_component_state_defaults_to_stock():
    status, lifecycle = assignment_component_state()
    assert status == STATUS_STOCK
    assert lifecycle == LIFECYCLE_STOCK
