from fastapi import APIRouter
from app.api.routes import users, auth

router = APIRouter()

router.include_router(users.router, prefix="/users", tags=["user"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])

#dependencies=[Depends(get_current_user)]  # All routes in this router will require auth
# - add this for routes with all endpoints protected