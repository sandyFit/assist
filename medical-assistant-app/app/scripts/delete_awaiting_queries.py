from app.db.database import engine
from sqlmodel import Session, select
from app.models import Query, QueryStatus, AISuggestion, File

def delete_awaiting_review():
    with Session(engine) as session:
        # Get queries awaiting review
        queries = session.exec(
            select(Query).where(Query.status == QueryStatus.AWAITING_REVIEW)
        ).all()

        count = len(queries)
        print(f"🗑 Found {count} awaiting_review queries")

        for query in queries:
            # Delete related files
            for file in query.files:
                session.delete(file)

            # Delete related AI suggestion
            if query.ai_suggestion:
                session.delete(query.ai_suggestion)

            # Delete the query itself
            session.delete(query)

        session.commit()
        print(f"✅ Deleted {count} queries + their files + AI suggestions")

if __name__ == "__main__":
    delete_awaiting_review()
