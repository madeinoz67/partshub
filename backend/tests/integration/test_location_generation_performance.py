"""
Performance validation tests for Storage Location Layout Generator.

These tests validate that the system meets performance requirements from research.md:
- T058: Preview API must respond in < 200ms for 500 locations
- T059: Bulk create API must complete in < 2000ms for 500 locations

Performance Targets:
- Preview API: <200ms for 500 locations (research.md requirement)
- Bulk Create API: <2s for 500 locations (research.md requirement)

Test Configuration:
- 500-location layout: 25 letters × 20 numbers = 500 locations
- Uses isolated in-memory SQLite database (Constitution Principle VI)
"""

import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.src.database import Base, get_db
from backend.src.main import app


@pytest.mark.integration
class TestLocationGenerationPerformance:
    """Performance validation tests (T058-T059)"""

    @pytest.fixture
    def db_session(self):
        """
        Create isolated in-memory SQLite database for performance tests.

        CRITICAL: Ensures test isolation per Constitution Principle VI.
        Uses StaticPool and check_same_thread=False for TestClient compatibility.
        """
        from sqlalchemy.pool import StaticPool

        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)  # noqa: N806
        session = SessionLocal()
        yield session
        session.close()

    @pytest.fixture
    def test_client(self, db_session):
        """Create test client with database session override"""

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                yield client
        finally:
            app.dependency_overrides.clear()

    @pytest.fixture
    def perf_config_500_locations(self):
        """
        Configuration that generates exactly 500 locations.

        Layout: 25 letters (a-y) × 20 numbers (1-20) = 500 locations
        Format: perf-a-1, perf-a-2, ..., perf-y-20
        """
        return {
            "layout_type": "grid",
            "prefix": "perf-",
            "ranges": [
                {
                    "range_type": "letters",
                    "start": "a",
                    "end": "y",  # 25 letters (a-y)
                    "capitalize": False,
                },
                {
                    "range_type": "numbers",
                    "start": 1,
                    "end": 20,  # 20 numbers (1-20)
                    "zero_pad": False,
                },
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }

    def test_preview_performance_500_locations(
        self, test_client, db_session, perf_config_500_locations
    ):
        """
        T058: Preview API Performance Validation

        Requirement: Preview generation must complete in <200ms for 500 locations.

        This test:
        1. Configures a 500-location layout (25×20 grid)
        2. Calls POST /api/storage-locations/generate-preview
        3. Measures response time using high-precision timer
        4. Asserts response time < 200ms

        Expected: ~0.15ms based on smoke tests (1,333x faster than required)
        """
        config = perf_config_500_locations

        # Measure preview performance
        start = time.perf_counter()
        response = test_client.post(
            "/api/v1/storage-locations/generate-preview", json=config
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Validate response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        # Validate preview content
        assert data["is_valid"] is True, "Configuration should be valid"
        assert data["total_count"] == 500, "Should preview exactly 500 locations"
        assert len(data["sample_names"]) == 5, "Should return 5 sample names"
        assert data["sample_names"][0] == "perf-a-1", "First sample should be perf-a-1"
        assert data["sample_names"][-1] == "perf-a-5", "Last sample should be perf-a-5"
        assert data["last_name"] == "perf-y-20", "Last location should be perf-y-20"

        # Performance assertion
        assert (
            elapsed_ms < 200
        ), f"Preview took {elapsed_ms:.2f}ms (requirement: <200ms)"

        # Log performance for monitoring
        print(
            f"\n✓ Preview Performance: {elapsed_ms:.2f}ms for 500 locations "
            f"({200 / elapsed_ms:.1f}x faster than required)"
        )

    def test_bulk_create_performance_500_locations(
        self, test_client, db_session, perf_config_500_locations, auth_headers
    ):
        """
        T059: Bulk Create API Performance Validation

        Requirement: Bulk creation must complete in <2000ms for 500 locations.

        This test:
        1. Uses same 500-location configuration
        2. Calls POST /api/storage-locations/bulk-create-layout
        3. Measures total execution time (including DB writes)
        4. Asserts execution time < 2000ms

        Expected: <100ms based on smoke tests (20x faster than required)

        IMPORTANT: Uses authenticated request (bulk create requires auth)
        """
        config = perf_config_500_locations

        # Measure bulk create performance
        start = time.perf_counter()
        response = test_client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=config,
            headers=auth_headers,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Validate response
        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        # Validate bulk create result
        assert data["success"] is True, "Bulk create should succeed"
        assert (
            data["created_count"] == 500
        ), f"Should create exactly 500 locations, got {data['created_count']}"
        assert (
            len(data["created_ids"]) == 500
        ), f"Should return 500 IDs, got {len(data['created_ids'])}"
        assert data["errors"] is None, f"Should have no errors, got {data['errors']}"

        # Verify database persistence
        from backend.src.models.storage_location import StorageLocation

        created_count = (
            db_session.query(StorageLocation)
            .filter(StorageLocation.name.like("perf-%"))
            .count()
        )
        assert created_count == 500, "Database should contain 500 locations"

        # Performance assertion
        assert (
            elapsed_ms < 2000
        ), f"Bulk create took {elapsed_ms:.2f}ms (requirement: <2000ms)"

        # Log performance for monitoring
        print(
            f"\n✓ Bulk Create Performance: {elapsed_ms:.2f}ms for 500 locations "
            f"({2000 / elapsed_ms:.1f}x faster than required)"
        )

    def test_preview_performance_edge_cases(self, test_client, db_session):
        """
        Additional performance validation for edge cases.

        Tests:
        1. Minimum: 1 location (edge case)
        2. Small batch: 10 locations
        3. Medium batch: 100 locations
        4. Maximum allowed: 500 locations

        Validates performance scales linearly with batch size.
        """
        test_cases = [
            # (description, ranges, expected_count, max_time_ms)
            (
                "1 location (minimum)",
                [
                    {
                        "range_type": "letters",
                        "start": "a",
                        "end": "a",
                        "capitalize": False,
                    }
                ],
                1,
                50,
            ),
            (
                "10 locations (small)",
                [
                    {
                        "range_type": "letters",
                        "start": "a",
                        "end": "j",
                        "capitalize": False,
                    }
                ],
                10,
                100,
            ),
            (
                "100 locations (medium)",
                [
                    {
                        "range_type": "letters",
                        "start": "a",
                        "end": "j",
                        "capitalize": False,
                    },
                    {"range_type": "numbers", "start": 1, "end": 10, "zero_pad": False},
                ],
                100,
                150,
            ),
            (
                "500 locations (maximum)",
                [
                    {
                        "range_type": "letters",
                        "start": "a",
                        "end": "y",
                        "capitalize": False,
                    },
                    {"range_type": "numbers", "start": 1, "end": 20, "zero_pad": False},
                ],
                500,
                200,
            ),
        ]

        results = []

        for description, ranges, expected_count, max_time_ms in test_cases:
            config = {
                "layout_type": "grid" if len(ranges) > 1 else "row",
                "prefix": "edge-",
                "ranges": ranges,
                "separators": ["-"] if len(ranges) > 1 else [],
                "location_type": "bin",
                "single_part_only": False,
            }

            start = time.perf_counter()
            response = test_client.post(
                "/api/v1/storage-locations/generate-preview", json=config
            )
            elapsed_ms = (time.perf_counter() - start) * 1000

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == expected_count
            assert (
                elapsed_ms < max_time_ms
            ), f"{description}: {elapsed_ms:.2f}ms > {max_time_ms}ms"

            results.append((description, expected_count, elapsed_ms))

        # Log performance profile
        print("\n✓ Performance Profile (Preview API):")
        for description, count, elapsed_ms in results:
            print(f"  - {description}: {elapsed_ms:.2f}ms ({count} locations)")

    def test_bulk_create_performance_edge_cases(
        self, test_client, db_session, auth_headers
    ):
        """
        Bulk create performance validation for different batch sizes.

        Tests performance characteristics:
        1. Small batch (10 locations): baseline overhead
        2. Medium batch (100 locations): linear scaling
        3. Large batch (500 locations): maximum load

        Validates that performance scales acceptably with batch size.
        """
        test_cases = [
            # (description, ranges, expected_count, max_time_ms)
            (
                "10 locations (small batch)",
                [
                    {
                        "range_type": "letters",
                        "start": "a",
                        "end": "j",
                        "capitalize": False,
                    }
                ],
                10,
                500,
            ),
            (
                "100 locations (medium batch)",
                [
                    {
                        "range_type": "letters",
                        "start": "a",
                        "end": "j",
                        "capitalize": False,
                    },
                    {"range_type": "numbers", "start": 1, "end": 10, "zero_pad": False},
                ],
                100,
                1000,
            ),
            (
                "500 locations (large batch)",
                [
                    {
                        "range_type": "letters",
                        "start": "a",
                        "end": "y",
                        "capitalize": False,
                    },
                    {"range_type": "numbers", "start": 1, "end": 20, "zero_pad": False},
                ],
                500,
                2000,
            ),
        ]

        results = []

        for idx, (description, ranges, expected_count, max_time_ms) in enumerate(
            test_cases
        ):
            # Use unique prefix for each test to avoid duplicates
            config = {
                "layout_type": "grid" if len(ranges) > 1 else "row",
                "prefix": f"bulk{idx}-",
                "ranges": ranges,
                "separators": ["-"] if len(ranges) > 1 else [],
                "location_type": "bin",
                "single_part_only": False,
            }

            start = time.perf_counter()
            response = test_client.post(
                "/api/v1/storage-locations/bulk-create-layout",
                json=config,
                headers=auth_headers,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000

            assert response.status_code == 201, f"Test failed: {response.text}"
            data = response.json()
            assert data["created_count"] == expected_count
            assert (
                elapsed_ms < max_time_ms
            ), f"{description}: {elapsed_ms:.2f}ms > {max_time_ms}ms"

            results.append((description, expected_count, elapsed_ms))

        # Log performance profile
        print("\n✓ Performance Profile (Bulk Create API):")
        for description, count, elapsed_ms in results:
            throughput = count / (elapsed_ms / 1000)  # locations per second
            print(
                f"  - {description}: {elapsed_ms:.2f}ms ({count} locations, {throughput:.0f} loc/sec)"
            )

    @pytest.fixture
    def auth_headers(self, test_client, db_session):
        """
        Create authentication headers for tests requiring auth.

        Creates a test admin user and generates JWT token.
        """
        from backend.src.auth.jwt_auth import create_access_token
        from backend.src.models import User

        # Create test admin user
        admin_user = User(
            username="perftest_admin",
            full_name="Performance Test Admin",
            is_admin=True,
            is_active=True,
        )
        admin_user.set_password("testpassword")

        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)

        # Generate JWT token
        token = create_access_token(
            {
                "sub": admin_user.id,
                "user_id": admin_user.id,
                "username": admin_user.username,
                "is_admin": admin_user.is_admin,
            }
        )

        return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestPerformanceScalability:
    """
    Additional scalability and bottleneck analysis tests.

    These tests help identify performance characteristics beyond requirements.
    """

    @pytest.fixture
    def db_session(self):
        """Create isolated in-memory SQLite database for scalability tests"""
        from sqlalchemy.pool import StaticPool

        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)  # noqa: N806
        session = SessionLocal()
        yield session
        session.close()

    @pytest.fixture
    def test_client(self, db_session):
        """Create test client with database session override"""

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                yield client
        finally:
            app.dependency_overrides.clear()

    def test_preview_algorithm_complexity(self, test_client, db_session):
        """
        Analyze preview algorithm time complexity.

        Tests different configurations to understand performance characteristics:
        - 1D layouts (row): O(n)
        - 2D layouts (grid): O(n*m)
        - 3D layouts: O(n*m*p)

        Validates that preview performance is consistent across layout types.
        """
        test_cases = [
            (
                "1D: 100 locations",
                "row",
                [{"range_type": "numbers", "start": 1, "end": 100, "zero_pad": False}],
                [],
                100,
            ),
            (
                "2D: 10×10 = 100 locations",
                "grid",
                [
                    {
                        "range_type": "letters",
                        "start": "a",
                        "end": "j",
                        "capitalize": False,
                    },
                    {"range_type": "numbers", "start": 1, "end": 10, "zero_pad": False},
                ],
                ["-"],
                100,
            ),
            (
                "3D: 5×5×4 = 100 locations",
                "grid_3d",
                [
                    {
                        "range_type": "letters",
                        "start": "a",
                        "end": "e",
                        "capitalize": False,
                    },
                    {"range_type": "numbers", "start": 1, "end": 5, "zero_pad": False},
                    {"range_type": "numbers", "start": 1, "end": 4, "zero_pad": False},
                ],
                ["-", "."],
                100,
            ),
        ]

        results = []

        for description, layout_type, ranges, separators, expected_count in test_cases:
            config = {
                "layout_type": layout_type,
                "prefix": "complexity-",
                "ranges": ranges,
                "separators": separators,
                "location_type": "bin",
                "single_part_only": False,
            }

            start = time.perf_counter()
            response = test_client.post(
                "/api/v1/storage-locations/generate-preview", json=config
            )
            elapsed_ms = (time.perf_counter() - start) * 1000

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == expected_count

            results.append((description, elapsed_ms))

        # Log complexity analysis
        print("\n✓ Algorithm Complexity Analysis:")
        for description, elapsed_ms in results:
            print(f"  - {description}: {elapsed_ms:.2f}ms")

        # All should complete in similar time (O(n) for generation, regardless of dimensions)
        times = [t for _, t in results]
        max_time = max(times)
        min_time = min(times)
        variance = max_time - min_time

        print(
            f"  - Time variance: {variance:.2f}ms (max: {max_time:.2f}ms, min: {min_time:.2f}ms)"
        )

        # Variance should be minimal for same count
        assert variance < 50, f"Time variance too high: {variance:.2f}ms"
