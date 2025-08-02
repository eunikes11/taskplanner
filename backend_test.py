#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Kid-Friendly Task Planner
Tests authentication, task management, and all API endpoints
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta

# Backend URL from environment
BACKEND_URL = "https://48d75d83-1859-4f4a-a9fd-7e015b313cd1.preview.emergentagent.com/api"

class TaskPlannerTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.username = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
    
    def make_request(self, method, endpoint, data=None, headers=None, expect_success=True):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def get_auth_headers(self):
        """Get authorization headers"""
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        print("\n=== Testing User Registration ===")
        
        # Use timestamp to ensure unique username
        import time
        timestamp = str(int(time.time()))
        unique_username = f"student_{timestamp}"
        
        # Test successful registration
        user_data = {
            "username": unique_username,
            "password": "myschoolwork123"
        }
        
        response = self.make_request("POST", "/auth/register", user_data)
        
        if response and response.status_code == 200:
            data = response.json()
            required_fields = ["access_token", "token_type", "user_id", "username"]
            
            if all(field in data for field in required_fields):
                self.auth_token = data["access_token"]
                self.user_id = data["user_id"]
                self.username = data["username"]
                self.log_test("User Registration", True, f"Successfully registered user: {data['username']}")
            else:
                self.log_test("User Registration", False, "Missing required fields in response", data)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("User Registration", False, f"Registration failed: {error_msg}")
        
        # Test duplicate username
        response = self.make_request("POST", "/auth/register", user_data)
        if response and response.status_code == 400:
            self.log_test("Duplicate Username Prevention", True, "Correctly rejected duplicate username")
        else:
            self.log_test("Duplicate Username Prevention", False, "Should reject duplicate usernames")
    
    def test_user_login(self):
        """Test user login endpoint"""
        print("\n=== Testing User Login ===")
        
        # Test successful login with the registered user
        login_data = {
            "username": self.username,
            "password": "myschoolwork123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        
        if response and response.status_code == 200:
            data = response.json()
            if "access_token" in data and data["username"] == self.username:
                self.log_test("User Login", True, f"Successfully logged in user: {data['username']}")
                # Update token for subsequent tests
                self.auth_token = data["access_token"]
            else:
                self.log_test("User Login", False, "Invalid login response format", data)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("User Login", False, f"Login failed: {error_msg}")
        
        # Test invalid credentials
        invalid_login = {
            "username": self.username,
            "password": "wrongpassword"
        }
        
        response = self.make_request("POST", "/auth/login", invalid_login)
        if response and response.status_code == 401:
            self.log_test("Invalid Login Prevention", True, "Correctly rejected invalid credentials")
        else:
            self.log_test("Invalid Login Prevention", False, "Should reject invalid credentials")
    
    def test_get_current_user(self):
        """Test get current user endpoint"""
        print("\n=== Testing Get Current User ===")
        
        if not self.auth_token:
            self.log_test("Get Current User", False, "No auth token available")
            return
        
        response = self.make_request("GET", "/auth/me", headers=self.get_auth_headers())
        
        if response and response.status_code == 200:
            data = response.json()
            if "user_id" in data and "username" in data:
                self.log_test("Get Current User", True, f"Retrieved user info: {data['username']}")
            else:
                self.log_test("Get Current User", False, "Missing user info in response", data)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get Current User", False, f"Failed to get user info: {error_msg}")
        
        # Test without authentication
        response = self.make_request("GET", "/auth/me")
        if response and response.status_code in [401, 403]:
            self.log_test("Auth Protection", True, "Correctly requires authentication")
        else:
            self.log_test("Auth Protection", False, "Should require authentication")
    
    def test_task_creation(self):
        """Test task creation endpoint"""
        print("\n=== Testing Task Creation ===")
        
        if not self.auth_token:
            self.log_test("Task Creation", False, "No auth token available")
            return
        
        # Create multiple tasks with kid-friendly content
        tasks_to_create = [
            {"title": "Brush my teeth before school"},
            {"title": "Pack my backpack with homework"},
            {"title": "Feed my pet hamster"},
            {"title": "Practice piano for 15 minutes"},
            {"title": "Clean up my room"}
        ]
        
        self.created_tasks = []
        
        for task_data in tasks_to_create:
            response = self.make_request("POST", "/tasks", task_data, headers=self.get_auth_headers())
            
            if response and response.status_code == 200:
                data = response.json()
                required_fields = ["id", "user_id", "title", "completed", "order_index", "created_at"]
                
                if all(field in data for field in required_fields):
                    self.created_tasks.append(data)
                    self.log_test("Task Creation", True, f"Created task: '{data['title']}'")
                else:
                    self.log_test("Task Creation", False, "Missing required fields in task", data)
            else:
                error_msg = response.json().get("detail", "Unknown error") if response else "No response"
                self.log_test("Task Creation", False, f"Failed to create task: {error_msg}")
        
        # Test task creation without authentication
        response = self.make_request("POST", "/tasks", {"title": "Unauthorized task"})
        if response and response.status_code in [401, 403]:
            self.log_test("Task Creation Auth Protection", True, "Correctly requires authentication")
        else:
            self.log_test("Task Creation Auth Protection", False, "Should require authentication")
    
    def test_get_tasks(self):
        """Test get tasks endpoint"""
        print("\n=== Testing Get Tasks ===")
        
        if not self.auth_token:
            self.log_test("Get Tasks", False, "No auth token available")
            return
        
        response = self.make_request("GET", "/tasks", headers=self.get_auth_headers())
        
        if response and response.status_code == 200:
            tasks = response.json()
            
            if isinstance(tasks, list):
                self.log_test("Get Tasks", True, f"Retrieved {len(tasks)} tasks")
                
                # Verify tasks are sorted by order_index
                if len(tasks) > 1:
                    is_sorted = all(tasks[i]["order_index"] <= tasks[i+1]["order_index"] 
                                  for i in range(len(tasks)-1))
                    self.log_test("Task Ordering", is_sorted, "Tasks sorted by order_index" if is_sorted else "Tasks not properly sorted")
                
                # Store tasks for further testing
                self.retrieved_tasks = tasks
            else:
                self.log_test("Get Tasks", False, "Response is not a list", tasks)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get Tasks", False, f"Failed to get tasks: {error_msg}")
    
    def test_task_update(self):
        """Test task update endpoint"""
        print("\n=== Testing Task Update ===")
        
        if not self.auth_token or not hasattr(self, 'retrieved_tasks') or not self.retrieved_tasks:
            self.log_test("Task Update", False, "No tasks available for testing")
            return
        
        task_to_update = self.retrieved_tasks[0]
        task_id = task_to_update["id"]
        
        # Test updating task completion
        update_data = {"completed": True}
        response = self.make_request("PUT", f"/tasks/{task_id}", update_data, headers=self.get_auth_headers())
        
        if response and response.status_code == 200:
            updated_task = response.json()
            if updated_task["completed"] == True and "completed_at" in updated_task:
                self.log_test("Task Completion Update", True, f"Successfully marked task as completed")
            else:
                self.log_test("Task Completion Update", False, "Task completion not properly updated", updated_task)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Task Completion Update", False, f"Failed to update task: {error_msg}")
        
        # Test updating task title
        update_data = {"title": "Brush my teeth AND floss before school"}
        response = self.make_request("PUT", f"/tasks/{task_id}", update_data, headers=self.get_auth_headers())
        
        if response and response.status_code == 200:
            updated_task = response.json()
            if updated_task["title"] == update_data["title"]:
                self.log_test("Task Title Update", True, "Successfully updated task title")
            else:
                self.log_test("Task Title Update", False, "Task title not properly updated", updated_task)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Task Title Update", False, f"Failed to update task title: {error_msg}")
        
        # Test updating non-existent task
        response = self.make_request("PUT", "/tasks/non-existent-id", {"completed": True}, headers=self.get_auth_headers())
        if response and response.status_code == 404:
            self.log_test("Non-existent Task Update", True, "Correctly handled non-existent task")
        else:
            self.log_test("Non-existent Task Update", False, "Should return 404 for non-existent task")
    
    def test_task_reordering(self):
        """Test task reordering endpoint"""
        print("\n=== Testing Task Reordering ===")
        
        if not self.auth_token or not hasattr(self, 'retrieved_tasks') or len(self.retrieved_tasks) < 2:
            self.log_test("Task Reordering", False, "Need at least 2 tasks for reordering test")
            return
        
        # Create reorder data - reverse the order
        task_orders = []
        for i, task in enumerate(reversed(self.retrieved_tasks)):
            task_orders.append({"id": task["id"], "order_index": i})
        
        reorder_data = {"task_orders": task_orders}
        response = self.make_request("POST", "/tasks/reorder", reorder_data, headers=self.get_auth_headers())
        
        if response and response.status_code == 200:
            self.log_test("Task Reordering", True, "Successfully reordered tasks")
            
            # Verify the reordering worked by getting tasks again
            response = self.make_request("GET", "/tasks", headers=self.get_auth_headers())
            if response and response.status_code == 200:
                reordered_tasks = response.json()
                # Check if first task is now what was previously last
                if reordered_tasks[0]["id"] == self.retrieved_tasks[-1]["id"]:
                    self.log_test("Task Reorder Verification", True, "Task order successfully changed")
                else:
                    self.log_test("Task Reorder Verification", False, "Task order not properly updated")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Task Reordering", False, f"Failed to reorder tasks: {error_msg}")
    
    def test_task_deletion(self):
        """Test task deletion endpoint"""
        print("\n=== Testing Task Deletion ===")
        
        if not self.auth_token or not hasattr(self, 'retrieved_tasks') or not self.retrieved_tasks:
            self.log_test("Task Deletion", False, "No tasks available for deletion test")
            return
        
        task_to_delete = self.retrieved_tasks[-1]  # Delete the last task
        task_id = task_to_delete["id"]
        
        response = self.make_request("DELETE", f"/tasks/{task_id}", headers=self.get_auth_headers())
        
        if response and response.status_code == 200:
            self.log_test("Task Deletion", True, f"Successfully deleted task: '{task_to_delete['title']}'")
            
            # Verify task is actually deleted
            response = self.make_request("GET", "/tasks", headers=self.get_auth_headers())
            if response and response.status_code == 200:
                remaining_tasks = response.json()
                task_still_exists = any(task["id"] == task_id for task in remaining_tasks)
                if not task_still_exists:
                    self.log_test("Task Deletion Verification", True, "Task successfully removed from database")
                else:
                    self.log_test("Task Deletion Verification", False, "Task still exists after deletion")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Task Deletion", False, f"Failed to delete task: {error_msg}")
        
        # Test deleting non-existent task
        response = self.make_request("DELETE", "/tasks/non-existent-id", headers=self.get_auth_headers())
        if response and response.status_code == 404:
            self.log_test("Non-existent Task Deletion", True, "Correctly handled non-existent task deletion")
        else:
            self.log_test("Non-existent Task Deletion", False, "Should return 404 for non-existent task")
    
    def test_task_statistics(self):
        """Test task statistics endpoint"""
        print("\n=== Testing Task Statistics ===")
        
        if not self.auth_token:
            self.log_test("Task Statistics", False, "No auth token available")
            return
        
        response = self.make_request("GET", "/tasks/stats", headers=self.get_auth_headers())
        
        if response and response.status_code == 200:
            stats = response.json()
            required_fields = ["total_tasks", "completed_tasks", "remaining_tasks", "completion_percentage"]
            
            if all(field in stats for field in required_fields):
                self.log_test("Task Statistics", True, f"Retrieved stats: {stats}")
                
                # Verify statistics make sense
                total = stats["total_tasks"]
                completed = stats["completed_tasks"]
                remaining = stats["remaining_tasks"]
                percentage = stats["completion_percentage"]
                
                if total == completed + remaining:
                    self.log_test("Statistics Calculation", True, "Task counts are consistent")
                else:
                    self.log_test("Statistics Calculation", False, f"Inconsistent counts: {total} != {completed} + {remaining}")
                
                if total > 0:
                    expected_percentage = (completed / total) * 100
                    if abs(percentage - expected_percentage) < 0.01:  # Allow for floating point precision
                        self.log_test("Percentage Calculation", True, "Completion percentage is correct")
                    else:
                        self.log_test("Percentage Calculation", False, f"Wrong percentage: {percentage} != {expected_percentage}")
                
            else:
                self.log_test("Task Statistics", False, "Missing required fields in stats", stats)
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Task Statistics", False, f"Failed to get statistics: {error_msg}")
    
    def test_authentication_protection(self):
        """Test that all endpoints properly require authentication"""
        print("\n=== Testing Authentication Protection ===")
        
        protected_endpoints = [
            ("GET", "/tasks"),
            ("POST", "/tasks"),
            ("GET", "/tasks/stats"),
            ("GET", "/auth/me")
        ]
        
        for method, endpoint in protected_endpoints:
            response = self.make_request(method, endpoint, {"title": "test"} if method == "POST" else None)
            
            if response and response.status_code in [401, 403]:
                self.log_test(f"Auth Protection {method} {endpoint}", True, "Correctly requires authentication")
            else:
                self.log_test(f"Auth Protection {method} {endpoint}", False, "Should require authentication")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Kid-Friendly Task Planner Backend API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run tests in logical order
        self.test_user_registration()
        self.test_user_login()
        self.test_get_current_user()
        self.test_task_creation()
        self.test_get_tasks()
        self.test_task_update()
        self.test_task_reordering()
        self.test_task_statistics()
        self.test_task_deletion()
        self.test_authentication_protection()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        return failed_tests == 0

if __name__ == "__main__":
    tester = TaskPlannerTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 All tests passed! Backend API is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1)