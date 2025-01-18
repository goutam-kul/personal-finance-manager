import sys
import os 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, UploadFile, File
from sqlalchemy.sql import func
from app.models import Expense, Budget, engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from db.database import SessionLocal
import whisper

# Create a database session 
router = APIRouter()

# Whisper model for transcribing 
whisper_model = whisper.load_model("base")

# Pydantic modesl for request validation 
class ExpenseInput(BaseModel):
    amount: float
    category: str
    date: str

class BudgetInput(BaseModel):
    category: str
    limit: float

class UpdateBudget(BaseModel):
    new_limit: float

# Add an expense
@router.post("/expenses/")
def add_expense(expense: ExpenseInput):
    session = SessionLocal()
    try:
        # Check if budget exists for the category 
        budget = session.query(Budget).filter(Budget.category == expense.category).first()
        if budget:
            # Check if the month has changed
            last_expense = session.query(Expense).filter(
                Expense.category == expense.category
            ).order_by(Expense.date.desc()).first()
            if last_expense:
                last_month = last_expense.date.month
                last_year = last_expense.date.year
                current_month = datetime.strptime(expense.date, "%Y-%M-%d").month
                current_year = datetime.strptime(expense.date, "%Y-%m-%d").year

                # Reset current_total if the month has changed
                if last_year != current_year or last_month != current_month:
                    budget.current_total = 0

            # Check if adding the expense exceeds the budget
            if budget.current_total + expense.amount > budget.limit:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Adding this expense exceeds your budget for {expense.category}. You can update the budget and try again."
                    )
            
        # convert string datea to a python datetime.data object
        date_object = datetime.strptime(expense.date, "%Y-%m-%d").date()
        new_expense = Expense(amount=expense.amount, category=expense.category, date=date_object)
        session.add(new_expense)

        # Update the budget's current totat
        if budget:
            budget.current_total += expense.amount
        
        session.commit()
        return {"message": "Expense added successfully."}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


# Get expense summary
@router.get("/expenses/summary")
def get_expense_summary():
    session = SessionLocal()
    try:
        expenses = session.query(Expense).all()
        return [{"id": e.id, "amount": e.amount, "category": e.category, "date": e.date} for e in expenses]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally: 
        session.close()


# Set a budget
@router.post("/budget/")
def set_budget(budget: BudgetInput):
    session = SessionLocal()
    try:
        new_budget = Budget(category=budget.category, limit=budget.limit)
        session.add(new_budget)
        session.commit()
        return {"message": "Budget set successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@router.get("/budget/show")
def show_budget():
    session = SessionLocal()
    try:
        budgets = session.query(Budget).all()
        if not budgets:
            return {"message": "No budgets found"}
        
        # Serialzing the data 
        return [
            {
                "category": budget.category,
                "limit": budget.limit,
            }
            for budget in budgets
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()
        
# Budget remaining for a category 
@router.get("/budget/remaining/{category}")
def get_remaining_budget(category: str):
    session = SessionLocal()
    try:
        budget = session.query(Budget).filter(Budget.category == category).first()
        if not budget:
            raise HTTPException(status_code=404, detail=f"No budget found for category {category}")
        
        # Ensure current_total is not negative
        current_total = max(0, budget.current_total)
        remaining = budget.limit - current_total

        return {
            "category": category,
            "limit": budget.limit,
            "current_total": current_total,
            "remaining": remaining,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

# Get expense report from a month 
@router.get("/expenses/report/{year}/{month}")
def monthly_spending_report(year: int, month: int):
    session = SessionLocal()
    try:
        expenses = session.query(Expense).filter(
            Expense.date.between(f"{year}-{month:02d}-01", f"{year}-{month:02d}-31")
        ).all()
        
        report = {}
        for expense in expenses:
            if expense.category not in report:
                report[expense.category] = 0.0
            report[expense.category] += expense.amount

        return {"year": year, "month": month, "spending": report}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

# Delete an expense 
@router.delete("/expenses/{id}")
def delete_expense(id: int):
    session = SessionLocal()
    try:
        expense = session.query(Expense).filter(Expense.id == id).first()
        if not expense:
            raise HTTPException(status_code=400, detail=f"Expense with id {id} not found")
        
        # Update budget's current total if applicable
        budget = session.query(Budget).filter(Budget.category == expense.category).first()
        if budget:
            budget.current_total = max(0, budget.current_total - expense.amount)

        session.delete(expense)
        session.commit()
        return {"message": "Expense deleted succesfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

# Get category-wise summary
@router.get("/expenses/category-summary/")
def get_category_summary():
    session = SessionLocal()
    try:
        result = session.query(
            Expense.category,
            func.sum(Expense.amount).label("total")
        ).group_by(Expense.category).all()

        return [{"category": row[0], "amount": row[1]} for row in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


@router.get("/expenses/monthly-summary/")
def get_montly_summary():
    session = SessionLocal()
    try:
        result = session.query(
            func.strftime("%Y-%m", Expense.date).label("month"),
            func.sum(Expense.amount).label("total")
        ).group_by("month").all()

        # Convert "YYYY-MM" into "Month YYYY"
        formatted_result = []
        for row in result:
            month_date = datetime.strptime(row[0], "%Y-%m")
            formatted_result.append({
                "month": month_date.strftime("%B %Y"),
                "amount": row[1]
            })
        return formatted_result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()

@router.put("/budget/{category}")
def update_budget(category: str, request: UpdateBudget):
    session = SessionLocal()
    try:
        # Extract the new_limit from the request body
        new_limit = request.new_limit

        # Find the budget for the specified category
        budget = session.query(Budget).filter(Budget.category == category).first()
        if not budget:
            raise HTTPException(status_code=400, detail=f"No budget found for category {category}")
        
        # Update the budget
        budget.limit = new_limit
        session.commit()
        return {"message": f"budget for category {category} updated to new limit {new_limit}."}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


# Transcription end point
ACCEPTED_AUDIO_TYPE = {
    "audio/wav": ".wav",
    "audio/wave": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mpeg3": ".mp3",
    "audio/x-mpeg-3": ".mp3"
}

def validate_audio_file(file: UploadFile) -> bool:
    """Validate the uploaded file's content tyep."""
    return file.content_type in ACCEPTED_AUDIO_TYPE

def get_safe_temp_filepath(filename: str) -> str:
    """Generate a safe temporay file path."""
    base_name = os.path.basename(filename)
    return f"temp_{hash(base_name)}_{base_name}"

@router.post("/transcribe_audio/")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe an audio file using whisper.
    
    Args:
        file(UploadFile): The audio file to trnscribe(.wav or .mp3)
    
    Returns:
        dict: Contains the trancribed text.
    """
    try:
        print(f"File received: {file.filename}")
        print(f"Content type:  {file.content_type}")

        # Validate file type
        if not validate_audio_file(file):
            supported_formats = ", ".join(set(ACCEPTED_AUDIO_TYPE.values()))
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Supported formats are: {supported_formats}"
            )
        
        # Create a safe temporary file path
        temp_file_path = get_safe_temp_filepath(file.filename)

        try:
            # Save the file temporarily 
            content = await file.read()
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(content)

            print(f"File save at: {temp_file_path}")

            # Process the audio with whisper
            try:
                result = whisper_model.transcribe(temp_file_path)
                transcription = result['text']
                print("Transcription Successful.")

                return {
                    "status":  "success",
                    "transcription": transcription,
                    "filename": file.filename
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
        
        except Exception as processing_error:
            raise HTTPException(status_code=400, detail=f"Processing Failed: {str(processing_error)}")
        
        finally:
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    print(f"Temporary file removed: {temp_file_path}")
                except Exception as cleanup_error:
                    print(f"Warning: Failed to remove temporary file.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Unexpected error: {str(e)}"
        )