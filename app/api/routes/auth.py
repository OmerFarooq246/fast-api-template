from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.db.database import get_db
from app.core.security import create_access_token
from app.schemas.users import TokenSchema
from app.db.user_crud import user_crud

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/login", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await user_crud.authenticate(db, form_data.username, form_data.password)
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenSchema(access_token=access_token)