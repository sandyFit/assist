#!/usr/bin/env python

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session, SQLModel
from app.db.database import engine
from app.models import (
    Patient, Doctor, Query, File, AISuggestion, Review,
    QueryStatus, QueryPriority
)

# Create all tables
SQLModel.metadata.create_all(engine)

def parse_datetime(dt_str):
    """Parse datetime string from CSV"""
    if not dt_str:
        return datetime.now()
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.now()

def seed_patients(session):
    """Seed patients from CSV"""
    print("Seeding patients...")
    patients_file = Path(__file__).parent / "data" / "sample_patients.csv"
    
    with open(patients_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            patient = Patient(
                external_id=row["external_id"],
                name=row["name"],
                email=row["email"],
                age=int(row["age"]),
                medical_history=row["medical_history"]
            )
            session.add(patient)
    
    session.commit()
    print(f"Added {session.query(Patient).count()} patients")

def seed_doctors(session):
    """Seed doctors from CSV"""
    print("Seeding doctors...")
    doctors_file = Path(__file__).parent / "data" / "sample_doctors.csv"
    
    with open(doctors_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            doctor = Doctor(
                external_id=row["external_id"],
                name=row["name"],
                email=row["email"],
                specialty=row["specialty"]
            )
            session.add(doctor)
    
    session.commit()
    print(f"Added {session.query(Doctor).count()} doctors")

def seed_queries(session):
    """Seed queries from CSV"""
    print("Seeding queries...")
    queries_file = Path(__file__).parent / "data" / "sample_queries.csv"
    
    with open(queries_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            query = Query(
                patient_id=int(row["patient_id"]),
                content=row["content"],
                priority=QueryPriority[row["priority"]],
                status=QueryStatus[row["status"]],
                created_at=parse_datetime(row["created_at"])
            )
            session.add(query)
    
    session.commit()
    print(f"Added {session.query(Query).count()} queries")

def seed_suggestions(session):
    """Seed AI suggestions from CSV"""
    print("Seeding AI suggestions...")
    suggestions_file = Path(__file__).parent / "data" / "sample_suggestions.csv"
    
    with open(suggestions_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            suggestion = AISuggestion(
                query_id=int(row["query_id"]),
                content=row["content"],
                confidence_score=float(row["confidence_score"]),
                created_at=parse_datetime(row["created_at"])
            )
            session.add(suggestion)
    
    session.commit()
    print(f"Added {session.query(AISuggestion).count()} AI suggestions")

def seed_reviews(session):
    """Seed doctor reviews from CSV"""
    print("Seeding doctor reviews...")
    reviews_file = Path(__file__).parent / "data" / "sample_reviews.csv"
    
    with open(reviews_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            review = Review(
                query_id=int(row["query_id"]),
                doctor_id=int(row["doctor_id"]),
                content=row["content"],
                approved=row["approved"].lower() == "true",
                notes=row["notes"],
                created_at=parse_datetime(row["created_at"])
            )
            session.add(review)
    
    session.commit()
    print(f"Added {session.query(Review).count()} doctor reviews")

def seed_sample_files(session):
    """Seed sample files"""
    print("Seeding sample files...")
    
    # Create uploads directory if it doesn't exist
    uploads_dir = Path(__file__).parent / "data" / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    
    # Copy sample lab results to uploads directory
    sample_file = Path(__file__).parent / "data" / "sample_lab_results.txt"
    if sample_file.exists():
        # Create a file record in the database
        file = File(
            query_id=1,  # Associate with the first query
            filename="lab_results.txt",
            filepath=str(uploads_dir / "lab_results.txt"),
            filetype="text/plain",
            filesize=os.path.getsize(sample_file)
        )
        session.add(file)
        
        # Copy the file to uploads directory
        with open(sample_file, "r") as src, open(uploads_dir / "lab_results.txt", "w") as dst:
            dst.write(src.read())
    
    session.commit()
    print(f"Added {session.query(File).count()} files")

def main():
    """Main function to seed the database"""
    print("Starting database seeding...")
    
    with Session(engine) as session:
        # Check if database is already seeded
        if session.query(Patient).count() > 0:
            user_input = input("Database already contains data. Do you want to reset and reseed? (y/n): ")
            if user_input.lower() != 'y':
                print("Seeding cancelled.")
                return
            
            # Clear existing data
            session.query(Review).delete()
            session.query(AISuggestion).delete()
            session.query(File).delete()
            session.query(Query).delete()
            session.query(Doctor).delete()
            session.query(Patient).delete()
            session.commit()
        
        # Seed the database
        seed_patients(session)
        seed_doctors(session)
        seed_queries(session)
        seed_suggestions(session)
        seed_reviews(session)
        seed_sample_files(session)
    
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    main()