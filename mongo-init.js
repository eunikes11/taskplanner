// MongoDB initialization script
// This script runs when MongoDB container starts for the first time

// Switch to the task planner database
db = db.getSiblingDB('task_planner_db');

// Create collections with validation schemas
db.createCollection('users', {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["id", "username", "hashed_password", "created_at"],
         properties: {
            id: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            username: {
               bsonType: "string",
               minLength: 1,
               description: "must be a string and is required"
            },
            hashed_password: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            created_at: {
               bsonType: "date",
               description: "must be a date and is required"
            }
         }
      }
   }
});

db.createCollection('tasks', {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["id", "user_id", "title", "completed", "order_index", "task_date", "created_at"],
         properties: {
            id: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            user_id: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            title: {
               bsonType: "string",
               minLength: 1,
               description: "must be a string and is required"
            },
            completed: {
               bsonType: "bool",
               description: "must be a boolean and is required"
            },
            order_index: {
               bsonType: "int",
               description: "must be an integer and is required"
            },
            task_date: {
               bsonType: "string",
               pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
               description: "must be a string in YYYY-MM-DD format and is required"
            },
            created_at: {
               bsonType: "date",
               description: "must be a date and is required"
            },
            completed_at: {
               bsonType: ["date", "null"],
               description: "must be a date or null"
            }
         }
      }
   }
});

// Create indexes for better performance
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "id": 1 }, { unique: true });

db.tasks.createIndex({ "user_id": 1, "task_date": 1 });
db.tasks.createIndex({ "id": 1 }, { unique: true });
db.tasks.createIndex({ "user_id": 1, "task_date": 1, "order_index": 1 });

print("Database initialization completed successfully!");
print("Created collections: users, tasks");
print("Created indexes for optimized queries");