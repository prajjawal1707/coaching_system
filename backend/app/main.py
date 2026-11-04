
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from app.schemas.student import StudentResponse, FeeResponse

app = FastAPI(
    title="FeeFlow API",
    description="Fee Management System Backend",
    version="1.0.0"
)

# Allow our React frontend to communicate with FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

students = [
    {
        "id": "FF-1001",
        "name": "Aarav Sharma",
        "course": "JEE Advanced",
        "total_fees": 120000,
        "paid_fees": 90000,
        "attendance": 91
    },
    {
        "id": "FF-1002",
        "name": "Diya Verma",
        "course": "NEET",
        "total_fees": 100000,
        "paid_fees": 65000,
        "attendance": 68
    },
    {
        "id": "FF-1003",
        "name": "Kabir Singh",
        "course": "JEE Main",
        "total_fees": 90000,
        "paid_fees": 90000,
        "attendance": 96
    }
]


@app.get("/")
def home():
    return {
        "message": "Welcome to FeeFlow API",
        "status": "running"
    }


@app.get("/students", response_model=list[StudentResponse])
def get_students():
    return students


@app.get(
    "/students/{student_id}",
    response_model=StudentResponse
)
def get_student(student_id: str):
    for student in students:
        if student["id"] == student_id:
            return student

    raise HTTPException(
        status_code=404,
        detail="Student not found"
    )


@app.get(
    "/fees/{student_id}",
    response_model=FeeResponse
)
def get_student_fees(student_id: str):

    for student in students:
        if student["id"] == student_id:

            pending = (
                student["total_fees"]
                - student["paid_fees"]
            )

            return {
                "student_id": student["id"],
                "student_name": student["name"],
                "total_fees": student["total_fees"],
                "paid_fees": student["paid_fees"],
                "pending_fees": pending
            }

    raise HTTPException(
        status_code=404,
        detail="Student not found"
    )