from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

import schemas
from database import get_db, MovieModel, models
from schemas import MovieListResponseSchema, MovieDetailResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=schemas.MovieListResponseSchema)
async def read_movies(
        per_page: int = Query(10, ge=1, le=20),
        page: int = Query(1, ge=1),
        db: AsyncSession = Depends(get_db)
):

    total_items = await db.scalar(select(func.count()).select_from(models.MovieModel))
    total_pages = (total_items + per_page - 1) // per_page
    query = select(models.MovieModel).offset((page - 1) * per_page).limit(per_page)
    movie_list = await db.execute(query)
    movies = movie_list.scalars().all()
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None
    if not per_page or not page:
        raise HTTPException(
            status_code=422, detail=[
                {
                    "loc": ["query", "page"],
                    "msg": "ensure this value is greater than or equal to 1",
                    "type": "value_error.number.not_ge"
                }
            ]
        )
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    return {
        "movies": [MovieDetailResponseSchema.from_orm(movie) for movie in movies],
        "total_pages": total_pages,
        "total_items": total_items,
        "prev_page": prev_page,
        "next_page": next_page,
    }


@router.get("/movies/{film_id}/", response_model=MovieDetailResponseSchema)
async def get_film(film_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == film_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie
