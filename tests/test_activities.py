"""
Test suite for High School Activity Management API
Using AAA (Arrange-Act-Assert) pattern
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        # Arrange (setup)
        # No additional setup needed
        
        # Act (execute)
        response = client.get("/activities")
        
        # Assert (verify)
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 10
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_get_activities_includes_expected_fields(self, client):
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert set(activity_data.keys()) == expected_fields
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_get_activities_participants_are_strings(self, client):
        # Arrange
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        # Arrange
        expected_redirect = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        # Arrange
        activity_name = "Tennis Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_already_signed_up(self, client):
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_activity_not_found(self, client):
        # Arrange
        activity_name = "NonexistentActivity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_updates_participant_list(self, client):
        # Arrange
        activity_name = "Science Club"
        new_student = "newtestuser@mergington.edu"
        
        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_student}
        )
        activities_response = client.get("/activities")
        
        # Assert
        assert signup_response.status_code == 200
        activities = activities_response.json()
        assert new_student in activities[activity_name]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_student_not_signed_up(self, client):
        # Arrange
        activity_name = "Tennis Club"
        email = "notstudent@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_activity_not_found(self, client):
        # Arrange
        activity_name = "FakeActivity"
        email = "test@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_updates_participant_list(self, client):
        # Arrange
        activity_name = "Gym Class"
        new_student = "unregister_test@mergington.edu"
        
        # First sign up the student
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_student}
        )
        
        # Act
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": new_student}
        )
        activities_response = client.get("/activities")
        
        # Assert
        assert unregister_response.status_code == 200
        activities = activities_response.json()
        assert new_student not in activities[activity_name]["participants"]


class TestIntegration:
    """Integration tests for signup/unregister workflow"""

    def test_full_signup_and_unregister_workflow(self, client):
        # Arrange
        activity = "Theater Club"
        student = "workflow@mergington.edu"
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity]["participants"])
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": student}
        )
        after_signup = client.get("/activities").json()
        after_signup_count = len(after_signup[activity]["participants"])
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": student}
        )
        final = client.get("/activities").json()
        final_count = len(final[activity]["participants"])
        
        # Assert
        assert signup_response.status_code == 200
        assert after_signup_count == initial_count + 1
        assert unregister_response.status_code == 200
        assert final_count == initial_count

    def test_rereg_after_unregister(self, client):
        # Arrange
        activity = "Debate Team"
        email = "comeback@mergington.edu"
        
        # Act - Sign up
        signup1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Act - Unregister
        unregister = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Act - Sign up again
        signup2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert signup1.status_code == 200
        assert unregister.status_code == 200
        assert signup2.status_code == 200
