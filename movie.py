from flask import Flask, render_template, request, redirect
import csv

app = Flask(__name__)

# CSV 파일 경로
CSV_FILE = 'movie.csv'

# CSV 파일에서 영화 데이터 읽기
def read_movies_from_csv():
    movies = []
    try:
        with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                movies.append({
                    "id": row["id"],
                    "title": row["title"],
                    "genres": row["genres"],
                    "averageRating": float(row["averageRating"]),
                    "releaseYear": int(row["releaseYear"])
                })
    except FileNotFoundError:
        print(f"Error: {CSV_FILE} 파일을 찾을 수 없습니다.")
    return movies

# 고유한 장르 추출
def get_unique_genres(movies):
    genres = set()
    for movie in movies:
        for genre in movie['genres'].split(','):
            genres.add(genre.strip())
    return sorted(genres)

# 영화 목록 페이지
@app.route('/')
def show_movies():
    query = request.args.get('query', '').lower()
    sort_by = request.args.get('sort_by', 'default')  # 정렬 기준
    movies = read_movies_from_csv()

    if query:
        movies = [movie for movie in movies if query in movie['title'].lower()]

    if sort_by == "title":
        movies = sorted(movies, key=lambda x: x["title"].lower())

    # 통계 데이터 준비
    total_movies = len(movies)
    avg_rating = round(sum(m["averageRating"] for m in movies) / total_movies, 2) if total_movies > 0 else 0

    genres = get_unique_genres(movies)
    return render_template(
        'index.html',
        movies=movies,
        genres=genres,
        query=query,
        total_movies=total_movies,
        avg_rating=avg_rating
    )

# 장르별 영화 페이지
@app.route('/genre/<genre>')
def show_movies_by_genre(genre):
    query = request.args.get('query', '').lower()
    sort_by = request.args.get('sort_by', 'default')
    movies = read_movies_from_csv()

    # 장르별 필터링
    filtered_movies = [movie for movie in movies if genre.lower() in movie['genres'].lower()]

    if query:
        filtered_movies = [movie for movie in filtered_movies if query in movie['title'].lower()]

    if sort_by == "title":
        filtered_movies = sorted(filtered_movies, key=lambda x: x["title"].lower())

    return render_template('genre.html', genre=genre, movies=filtered_movies, query=query)

# 영화 세부 정보 페이지
@app.route('/movie/<movie_id>')
def show_movie_details(movie_id):
    movies = read_movies_from_csv()
    movie = next((m for m in movies if m["id"] == movie_id), None)
    
    if movie:
        movie_genres = set(genre.strip().lower() for genre in movie["genres"].split(','))

        # 추천 영화 찾기
        recommended_movies = []
        for m in movies:
            if m["id"] != movie_id:
                other_movie_genres = set(genre.strip().lower() for genre in m["genres"].split(','))
                genre_overlap = len(movie_genres.intersection(other_movie_genres))
                if genre_overlap > 0:
                    recommended_movies.append({
                        "movie": m,
                        "genre_overlap": genre_overlap
                    })

        # 장르 일치 개수를 기준으로 정렬, 이후 평점으로 정렬
        recommended_movies = sorted(
            recommended_movies,
            key=lambda x: (x["genre_overlap"], x["movie"]["averageRating"]),
            reverse=True
        )[:10]

        return render_template(
            'movie_details.html',
            movie=movie,
            recommended_movies=[rm["movie"] for rm in recommended_movies]
        )
    
    return redirect('/')

# 영화 수정 페이지
@app.route('/movie/<movie_id>/edit', methods=['GET', 'POST'])
def edit_movie(movie_id):
    movies = read_movies_from_csv()
    movie = next((m for m in movies if m["id"] == movie_id), None)

    if movie:
        if request.method == 'POST':
            movie['title'] = request.form.get('title', '').strip()
            movie['genres'] = request.form.get('genres', '').strip()
            movie['averageRating'] = float(request.form.get('averageRating', movie['averageRating']))
            movie['releaseYear'] = int(request.form.get('releaseYear', movie['releaseYear']))

            updated_movies = [m if m["id"] != movie_id else movie for m in movies]

            with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=["id", "title", "genres", "averageRating", "releaseYear"])
                writer.writeheader()
                writer.writerows(updated_movies)

            return redirect(f'/movie/{movie_id}')

        return render_template('edit_movie.html', movie=movie)

    return redirect('/')

# 영화 삭제
@app.route('/movie/<movie_id>/delete', methods=['POST'])
def delete_movie(movie_id):
    movies = read_movies_from_csv()
    movies = [movie for movie in movies if movie["id"] != movie_id]

    # CSV에 저장
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["id", "title", "genres", "averageRating", "releaseYear"])
        writer.writeheader()
        writer.writerows(movies)

    return redirect('/')

# 영화 추가 페이지
@app.route('/new/', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        genres = request.form.get('genres', '').strip()
        average_rating = float(request.form.get('averageRating', 0))
        release_year = int(request.form.get('releaseYear', 0))

        if not title or not genres:
            return "Title and genres are required", 400

        movies = read_movies_from_csv()
        new_id = str(int(max([m["id"] for m in movies], default=0)) + 1)

        new_movie = {
            "id": new_id,
            "title": title,
            "genres": genres,
            "averageRating": average_rating,
            "releaseYear": release_year
        }

        movies.append(new_movie)
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["id", "title", "genres", "averageRating", "releaseYear"])
            writer.writeheader()
            writer.writerows(movies)

        return redirect('/')
    return render_template('add_movie.html')

# 장르 통계 페이지
@app.route('/genre/<genre>/stat')
def genre_stat(genre):
    movies = read_movies_from_csv()
    genre_movies = [m for m in movies if genre.lower() in m["genres"].lower()]

    total_movies = len(genre_movies)
    avg_rating = round(sum(m["averageRating"] for m in genre_movies) / total_movies, 6) if total_movies > 0 else 0

    top_rated_movie = max(genre_movies, key=lambda m: m["averageRating"], default=None)

    rating_ranges = [(0, 2), (2, 4), (4, 6), (6, 8), (8, 10)]
    rating_distribution = []
    for low, high in rating_ranges:
        count = sum(1 for m in genre_movies if low <= m["averageRating"] < high)
        rating_distribution.append((f"{low}–{high}", count))

    return render_template(
        'genre_stat.html',
        genre=genre,
        total_movies=total_movies,
        avg_rating=avg_rating,
        top_rated_movie=top_rated_movie,
        rating_distribution=rating_distribution
    )

if __name__ == '__main__':
    app.debug = True
    app.run(host="127.0.0.1", port=5000)
