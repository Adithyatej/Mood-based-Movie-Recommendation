from flask import Flask,request, render_template,redirect,session,url_for
import pickle
import pandas as pd
import numpy
import h5py
import requests
from patsy import dmatrices
from surprise import accuracy

# class is used to parse a file containing ratings, data should be in structure - user ; item ; rating
from surprise.reader import Reader

# class for loading datasets
from surprise.dataset import Dataset

# for model tuning model hyper-parameters
from surprise.model_selection import GridSearchCV

# for splitting the rating data in train and test dataset
from surprise.model_selection import train_test_split

# for implementing similarity based recommendation system
from surprise.prediction_algorithms.knns import KNNBasic

# for implementing matrix factorization based recommendation system
from surprise.prediction_algorithms.matrix_factorization import SVD

from collections import defaultdict

# for implementing cross validation
from surprise.model_selection import KFold


movies=pd.read_csv('output.csv')            #reading movies_dataset
ratings=pd.read_csv('movie_ratings.csv')    #reading collaborative_dataset



email_list=list(set(ratings['email-id'].tolist()))

with h5py.File('similarity_genres_list.h5', 'r') as hf:
    similarity_genres = hf['similarity_genres_list'][:]

with h5py.File('similarity_overview_list.h5', 'r') as hf:
    similarity_overview = hf['similarity_overview_list'][:]

with h5py.File('similarity_language_list.h5', 'r') as hf:
    similarity_language = hf['similarity_language_list'][:]


with h5py.File('similarity_credits_list.h5', 'r') as hf:
    similarity_credits = hf['similarity_credits_list'][:]


index=pd.Series(movies.index,index=movies['title']).drop_duplicates()
# print(index)



#fetching poster
def fetch_poster(movie_id):
    try:
        url = "https://api.themoviedb.org/3/movie/{}?api_key=b14bfa3f5d81efac91412f1d4e90eeac".format(movie_id)
        data = requests.get(url).json()
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500" + poster_path
        else:
            return None  # Or a default poster URL
    except requests.exceptions.RequestException as e:
        print(f"Error fetching poster for movie ID {movie_id}: {e}")
        return None  # Or a default poster URL

#content based function
def content_based(movies_name,type_of_movies):
    # print(type_of_movies)
    idx = index[movies_name]
    print(idx)
    sorted_similar_movies_1=similarity_genres[idx][1:5]
    sorted_similar_movies_2=similarity_overview[idx][1:5]
    sorted_similar_movies_3= similarity_language[idx][1:5]
    sorted_similar_movies_4= similarity_credits[idx][1:5]


    sim_idx_1= [i[0] for i in sorted_similar_movies_1]
    sim_idx_2= [i[0] for i in sorted_similar_movies_2]
    sim_idx_3= [i[0] for i in sorted_similar_movies_3]
    sim_idx_4= [i[0] for i in sorted_similar_movies_4]
    

    if type_of_movies=="International Films":
        similar_movies=sim_idx_2+sim_idx_4+sim_idx_1+sim_idx_3
    else:
        similar_movies=sim_idx_3+sim_idx_4+sim_idx_2+sim_idx_1

    # print(similar_movies)
    mov = movies[['movieId', 'title','popularity']].iloc[similar_movies]
    mov.reset_index(drop=True, inplace=True)
    mov.drop_duplicates(inplace=True)

    return mov







def recommend(movies_name,type_of_movies,email):
    # print(movies_name)
    '''user_id=0
    if email in email_list:
        algo=train_collaborative(ratings)
        index=ratings.index[ratings['email-id'] == email].tolist()[0]
        user_id = ratings.iloc[index]['userId']
        movies=collaborative_based(ratings, user_id, 5,algo)
    else:
        movies=pd.DataFrame(columns=['movieId','title','popularity'])'''


    
    recommended_movies=[]
    recommended_movies_poster=[]
    recommended_id=[]
    recommended_pop=[]
    mov=content_based(movies_name,type_of_movies)

    
    
    mov=mov


    print(mov)

    for i in mov['title']:
        recommended_movies.append(i)
        

    for i in mov['movieId']:
        recommended_id.append(i)
        path=fetch_poster(i)
        recommended_movies_poster.append(path)
        #print(recommended_movies_poster)

    for i in mov['popularity']:
        recommended_pop.append(i)

    

    return recommended_id,recommended_movies,recommended_movies_poster,recommended_pop







def train_collaborative(ratings):
    reader = Reader(rating_scale=(0, 5))

    # loading the rating dataset
    data = Dataset.load_from_df(ratings[['email-id', 'movieId', 'rating']], reader)

    # splitting the data into train and test dataset
    trainset, testset = train_test_split(data, test_size=0.2, random_state=40)
    
    # using SVD matrix factorization
    algo_svd = SVD()

    # training the algorithm on the trainset
    algo_svd.fit(trainset)

    # predicting ratings for the testset
    predictions = algo_svd.test(testset)

    # computing RMSE on the testset
    print(accuracy.rmse(predictions))
    print(accuracy.mae(predictions))

    # set the parameter space to tune
    param_grid = {'n_epochs': [10,20,30], 'lr_all': [0.001, 0.005, 0.01],
              'reg_all': [0.06, 0.08, 0.006]}

    # performing 3-fold gridsearch cross validation
    gs = GridSearchCV(SVD, param_grid, measures=['rmse', 'mae'], cv=3, n_jobs=-1)

    # fitting data
    gs.fit(data)
    para=[]
    para=gs.best_params['rmse']
    # building the optimized SVD model using optimal hyperparameter search
    svd_algo_optimized = SVD(n_epochs=para['n_epochs'], lr_all=para['lr_all'], reg_all=para['reg_all'])

    # training the algorithm on the trainset
    svd_algo_optimized.fit(trainset)

    # predicting ratings for the testset
    predictions = svd_algo_optimized.test(testset)

    # computing RMSE
    print(accuracy.rmse(predictions))
    return svd_algo_optimized




def collaborative_based(data, user_id, top_n, algo):

    # creating an empty list to store the recommended movie ids
    recommendations = []
    ids=[]
    # creating an user item interactions matrix 
    user_item_interactions_matrix = data.pivot(index='userId', columns='movieId', values='rating')
    
    # extracting those movie ids which the user_id has not interacted yet
    non_interacted_movies = user_item_interactions_matrix.loc[user_id][user_item_interactions_matrix.loc[user_id].isnull()].index.tolist()
    
    # looping through each of the movie id which user_id has not interacted yet
    for item_id in non_interacted_movies:
        
        # predicting the ratings for those non interacted movie ids by this user
        est = algo.predict(user_id, item_id).est
        
        # appending the predicted ratings
        recommendations.append((item_id, est))

    # sorting the predicted ratings in descending order
    recommendations.sort(key=lambda x: x[1], reverse=True)
    ids= [i[0] for i in recommendations]
    ids=ids[:top_n]
    existing_ids = set(ids).intersection(set(movies['movieId']))  
    filtered_movies = movies.loc[movies['movieId'].isin(existing_ids)]
    
    return filtered_movies[['movieId','title','popularity']][:top_n]







