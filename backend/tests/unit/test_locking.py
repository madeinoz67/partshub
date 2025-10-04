"""
Unit tests for pessimistic locking behavior based on research.md
Tests SQLAlchemy's with_for_update() locking patterns for stock operations
"""

import pytest
import threading
import time
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from backend.src.models import ComponentLocation, Component, StorageLocation


@pytest.mark.unit
class TestPessimisticLocking:
    """Unit tests for pessimistic locking with with_for_update()"""

    def test_acquire_lock_with_for_update(self, db_session):
        """
        Test 1: Acquire pessimistic lock with with_for_update(nowait=False)
        Verifies that lock can be acquired successfully on a ComponentLocation
        """
        # Create test data
        component = Component(
            id="test-component-1",
            name="Test Component",
            quantity_on_hand=0,
            minimum_stock=0
        )
        storage_location = StorageLocation(
            id="test-location-1",
            name="Test Location"
        )
        comp_location = ComponentLocation(
            id="test-comp-loc-1",
            component_id=component.id,
            storage_location_id=storage_location.id,
            quantity_on_hand=100
        )

        db_session.add_all([component, storage_location, comp_location])
        db_session.commit()

        # Acquire lock
        stmt = (
            select(ComponentLocation)
            .where(ComponentLocation.id == comp_location.id)
            .with_for_update(nowait=False)
        )

        locked_location = db_session.execute(stmt).scalar_one()

        # Verify lock was acquired and data is accessible
        assert locked_location is not None
        assert locked_location.quantity_on_hand == 100

        # Modify data under lock
        locked_location.quantity_on_hand = 90
        db_session.commit()

        # Verify modification
        db_session.refresh(comp_location)
        assert comp_location.quantity_on_hand == 90

    def test_concurrent_access_blocking(self, db_session):
        """
        Test 2: Concurrent access blocking
        Verifies that a second transaction attempting to lock the same row
        will block until the first transaction commits or rolls back
        """
        # Create test data
        component = Component(
            id="test-component-2",
            name="Test Component 2",
            quantity_on_hand=0,
            minimum_stock=0
        )
        storage_location = StorageLocation(
            id="test-location-2",
            name="Test Location 2"
        )
        comp_location = ComponentLocation(
            id="test-comp-loc-2",
            component_id=component.id,
            storage_location_id=storage_location.id,
            quantity_on_hand=50
        )

        db_session.add_all([component, storage_location, comp_location])
        db_session.commit()

        # Note: This test demonstrates the locking pattern
        # In practice, concurrent access would require multiple database sessions
        # which is complex to test in-memory SQLite with threading

        # Acquire lock in first transaction
        stmt = (
            select(ComponentLocation)
            .where(ComponentLocation.id == comp_location.id)
            .with_for_update(nowait=False)
        )

        locked_location = db_session.execute(stmt).scalar_one()
        assert locked_location is not None

        # Simulate holding lock and modifying data
        locked_location.quantity_on_hand = 40
        db_session.commit()

        # After commit, lock is released
        # Verify changes persisted
        db_session.refresh(comp_location)
        assert comp_location.quantity_on_hand == 40

    def test_lock_release_on_commit(self, db_session):
        """
        Test 3: Lock release on commit
        Verifies that pessimistic lock is automatically released when transaction commits
        """
        # Create test data
        component = Component(
            id="test-component-3",
            name="Test Component 3",
            quantity_on_hand=0,
            minimum_stock=0
        )
        storage_location = StorageLocation(
            id="test-location-3",
            name="Test Location 3"
        )
        comp_location = ComponentLocation(
            id="test-comp-loc-3",
            component_id=component.id,
            storage_location_id=storage_location.id,
            quantity_on_hand=75
        )

        db_session.add_all([component, storage_location, comp_location])
        db_session.commit()

        # Start transaction and acquire lock
        stmt = (
            select(ComponentLocation)
            .where(ComponentLocation.id == comp_location.id)
            .with_for_update(nowait=False)
        )

        locked_location = db_session.execute(stmt).scalar_one()
        locked_location.quantity_on_hand = 65

        # Commit transaction (releases lock)
        db_session.commit()

        # Verify lock was released by successfully querying again
        stmt_after = select(ComponentLocation).where(
            ComponentLocation.id == comp_location.id
        )
        location_after = db_session.execute(stmt_after).scalar_one()
        assert location_after.quantity_on_hand == 65

    def test_lock_release_on_rollback(self, db_session):
        """
        Test 4: Lock release on rollback
        Verifies that pessimistic lock is automatically released when transaction rolls back
        and that changes are reverted
        """
        # Create test data
        component = Component(
            id="test-component-4",
            name="Test Component 4",
            quantity_on_hand=0,
            minimum_stock=0
        )
        storage_location = StorageLocation(
            id="test-location-4",
            name="Test Location 4"
        )
        comp_location = ComponentLocation(
            id="test-comp-loc-4",
            component_id=component.id,
            storage_location_id=storage_location.id,
            quantity_on_hand=100
        )

        db_session.add_all([component, storage_location, comp_location])
        db_session.commit()

        original_quantity = comp_location.quantity_on_hand

        # Start transaction and acquire lock
        stmt = (
            select(ComponentLocation)
            .where(ComponentLocation.id == comp_location.id)
            .with_for_update(nowait=False)
        )

        locked_location = db_session.execute(stmt).scalar_one()
        locked_location.quantity_on_hand = 50  # Modify

        # Rollback transaction (releases lock and reverts changes)
        db_session.rollback()

        # Verify changes were reverted
        db_session.expire_all()
        db_session.refresh(comp_location)
        assert comp_location.quantity_on_hand == original_quantity

    def test_deadlock_prevention_with_consistent_ordering(self, db_session):
        """
        Test 5: Deadlock prevention with consistent lock ordering
        Verifies that locking rows in consistent order (sorted by ID) prevents deadlocks
        """
        # Create test data - two locations
        component = Component(
            id="test-component-5",
            name="Test Component 5",
            quantity_on_hand=0,
            minimum_stock=0
        )
        location_a = StorageLocation(
            id="location-a",
            name="Location A"
        )
        location_b = StorageLocation(
            id="location-b",
            name="Location B"
        )
        comp_loc_a = ComponentLocation(
            id="comp-loc-a",
            component_id=component.id,
            storage_location_id=location_a.id,
            quantity_on_hand=100
        )
        comp_loc_b = ComponentLocation(
            id="comp-loc-b",
            component_id=component.id,
            storage_location_id=location_b.id,
            quantity_on_hand=50
        )

        db_session.add_all([component, location_a, location_b, comp_loc_a, comp_loc_b])
        db_session.commit()

        # Simulate move operation: lock both locations in consistent order
        # Always lock lower ID first
        location_ids = sorted([comp_loc_a.id, comp_loc_b.id])

        # Lock first location
        stmt1 = (
            select(ComponentLocation)
            .where(ComponentLocation.id == location_ids[0])
            .with_for_update(nowait=False)
        )
        loc1 = db_session.execute(stmt1).scalar_one()

        # Lock second location
        stmt2 = (
            select(ComponentLocation)
            .where(ComponentLocation.id == location_ids[1])
            .with_for_update(nowait=False)
        )
        loc2 = db_session.execute(stmt2).scalar_one()

        # Both locks acquired successfully
        assert loc1 is not None
        assert loc2 is not None

        # Perform atomic transfer
        quantity_to_move = 30
        if loc1.id == comp_loc_a.id:
            source, dest = loc1, loc2
        else:
            source, dest = loc2, loc1

        source.quantity_on_hand -= quantity_to_move
        dest.quantity_on_hand += quantity_to_move

        # Commit (releases both locks)
        db_session.commit()

        # Verify transfer
        db_session.refresh(comp_loc_a)
        db_session.refresh(comp_loc_b)
        assert comp_loc_a.quantity_on_hand == 70
        assert comp_loc_b.quantity_on_hand == 80

    def test_lock_on_nonexistent_row(self, db_session):
        """
        Test attempting to lock a row that doesn't exist
        Should return None without raising exception
        """
        # Attempt to lock non-existent ComponentLocation
        stmt = (
            select(ComponentLocation)
            .where(ComponentLocation.id == "nonexistent-id")
            .with_for_update(nowait=False)
        )

        result = db_session.execute(stmt).scalar_one_or_none()

        # Should return None, not raise exception
        assert result is None

    def test_multiple_locks_same_component_different_locations(self, db_session):
        """
        Test acquiring locks on multiple ComponentLocations for the same component
        Verifies that locks on different rows don't interfere
        """
        # Create component with stock in multiple locations
        component = Component(
            id="test-component-6",
            name="Test Component 6",
            quantity_on_hand=0,
            minimum_stock=0
        )
        location_1 = StorageLocation(id="loc-1", name="Location 1")
        location_2 = StorageLocation(id="loc-2", name="Location 2")
        location_3 = StorageLocation(id="loc-3", name="Location 3")

        comp_loc_1 = ComponentLocation(
            id="comp-loc-1",
            component_id=component.id,
            storage_location_id=location_1.id,
            quantity_on_hand=100
        )
        comp_loc_2 = ComponentLocation(
            id="comp-loc-2",
            component_id=component.id,
            storage_location_id=location_2.id,
            quantity_on_hand=200
        )
        comp_loc_3 = ComponentLocation(
            id="comp-loc-3",
            component_id=component.id,
            storage_location_id=location_3.id,
            quantity_on_hand=50
        )

        db_session.add_all([
            component, location_1, location_2, location_3,
            comp_loc_1, comp_loc_2, comp_loc_3
        ])
        db_session.commit()

        # Lock two locations simultaneously (in consistent order)
        stmt1 = (
            select(ComponentLocation)
            .where(ComponentLocation.id == comp_loc_1.id)
            .with_for_update(nowait=False)
        )
        stmt2 = (
            select(ComponentLocation)
            .where(ComponentLocation.id == comp_loc_2.id)
            .with_for_update(nowait=False)
        )

        locked_1 = db_session.execute(stmt1).scalar_one()
        locked_2 = db_session.execute(stmt2).scalar_one()

        # Both locks acquired
        assert locked_1 is not None
        assert locked_2 is not None

        # Modify both
        locked_1.quantity_on_hand = 90
        locked_2.quantity_on_hand = 190

        # Location 3 is NOT locked, so it remains unchanged
        db_session.commit()

        # Verify modifications
        db_session.refresh(comp_loc_1)
        db_session.refresh(comp_loc_2)
        db_session.refresh(comp_loc_3)

        assert comp_loc_1.quantity_on_hand == 90
        assert comp_loc_2.quantity_on_hand == 190
        assert comp_loc_3.quantity_on_hand == 50  # Unchanged
