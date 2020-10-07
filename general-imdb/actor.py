from matplotlib import pyplot as plt
import pandas as pd
from bs4 import BeautifulSoup
from statistics import mean
from requests import get
import numpy as np

#Since the data cleaning and wrangling process is unique to each `Actor`, we have to find and clean data within the initialization of the `Actor` object. 
class Actor:
    def __init__(self, actor_link):
        # INITIAL DATA
        # Finding the actor's IMDb page and getting the list of movies
        url = actor_link + '#actor'
        response = get(url)
        html_soup = BeautifulSoup(response.text, 'html.parser')
        movie_containers = html_soup.find_all('div', 'filmo-category-section')
        movie_containers = movie_containers[0]
        
        # YEARS
        all_years = movie_containers.find_all('span')
        self.year_list = []
        # Isolating the actual years from the rest of the things in the <span> objects from the html
        for year in all_years:
            self.year_list.append(str(year).split('\n')[1][1:])
        # If there is a range of years (for a TV show), we choose the latter year since ratings are most
        # likely reflective of the most recent iteration of the show. 
        for index, year in enumerate(self.year_list):
            if '-' in year:
                self.year_list[index] = year.split('-')[1]
            '''
            IMDb uses roman numerals to differentiate between movies of the same name that were
            made the same year; the three lines below address that issue (assuming we don't) run
            into any higher numerals; to address this, one can simply manually add a couple more
            and should be fine.
            Note that we do the higher numerals first so that we don't pick up the '/I' from a 
            '/II', for example.
            '''
            if '/I' in year or '/II' in year:  
                self.year_list[index] = year.split('/II')[0]
                self.year_list[index] = year.split('/I')[0]
            if year == '':
                self.year_list[index] = 0 #our NaN for missing years
            self.year_list[index] = int(self.year_list[index])
            
        # TITLES
        movie_list = movie_containers.find_all('b')
        self.title_list = []
        self.tag_list = []
        for item in movie_list:
            # We find the movie titles...
            self.title_list.append(str(item.find('a')).split('>')[-2][:-3])
            # ...And the IMDb tags for each title
            self.tag_list.append(str(item.find('a')).split('/')[2])
                        
        # RATINGS
        self.rating_list = []
        # We visit each of the actors' titles' pages to find their ratings
        for tag in self.tag_list:
            url = 'https://www.imdb.com/title/' + tag + '/'
            response = get(url)
            html_soup = BeautifulSoup(response.text, 'html.parser')
            rating_containers = html_soup.find_all('div','ratingValue')
            if rating_containers == []:
                self.rating_list.append(-1) # our NaN for ratings is -1
                continue
            rating_str = str(rating_containers[0].find_all('strong')[0])
            rating = float(rating_str.split(' based on ')[0][-3:])
            self.rating_list.append(rating)
            
        # AVERAGE        
        self.avg = mean([rating for rating in self.rating_list if rating > -1.0])
        
        #List of attributes that Actor has (and their types):
        '''
        year_list (list [int])
        title_list (list [str])
        tag_list (list [str])
        rating_list (list [float])
        avg (float)
        '''
        
    # Creates a DataFrame with the Actor's info in it
    def makeDf(self):
        return pd.DataFrame(list(zip(self.rating_list, self.year_list, self.title_list)), columns=['Ratings', 'Year', 'Title'])
        
    # graphType decides what type of graph the method will show (between scatter, bar, and plot)
    # withMean determines whether the user wants a red horizontal line through the graph to demonstrate where the mean is
    def getGraph(self, graphType='s', withMean=False):
        # The two lines below ensure that we aren't including our NaN values
        valid_years = [year for index,year in enumerate(self.year_list) if year > 1893 and self.rating_list[index] != -1.0]
        valid_ratings = [rating for index,rating in enumerate(self.rating_list) if rating > -1.0 and self.year_list[index] != 0]
        plt.xlabel('Year')
        
        if graphType not in ['scatter', 's', 'bar', 'b', 'plot', 'p']:
            print('Valid name not chosen for parameter graphType; displaying default scatterplot.')
            graphType='s'
            
        if graphType == 'scatter' or graphType == 's':
            plt.ylabel('Rating')
            x = valid_years
            y = valid_ratings 
            plt.scatter(x,y)
            
        elif graphType == 'bar' or graphType == 'b':
            plt.ylabel('Average Rating')
            unique_year_list = np.unique(np.array(valid_years)) # create a list of just unique years
            avg_rating_list = []
            for year in unique_year_list:
                avg_rating_list.append(mean([rating for index,rating in enumerate(valid_ratings) if valid_years[index] == year]))
            x = unique_year_list
            y = avg_rating_list
            plt.bar(x,y)
            
        elif graphType == 'plot' or graphType == 'p':
            plt.ylabel('Rating')
            unique_year_list = np.unique(np.array(valid_years))
            min_list,avg_list,max_list = [],[],[]
            # For each year that the Actor had a role, we take the ratings for that year and find the min, mean, and max
            for year in unique_year_list:
                ratings_per_year = [rating for index,rating in enumerate(valid_ratings) if valid_years[index] == year]
                min_list.append(min(ratings_per_year))
                avg_list.append(mean(ratings_per_year))
                max_list.append(max(ratings_per_year))
            plt.plot(unique_year_list, min_list, color='b', marker='o', label='Min')
            plt.plot(unique_year_list, avg_list, color='r', marker='o', label='Mean')
            plt.plot(unique_year_list, max_list, color='g', marker='o',label='Max')
            plt.legend()
            
        if withMean:
            if graphType not in ['plot','p']:
                plt.plot([min(x)-1, max(x)+1], [self.avg, self.avg], label='Average', c='r',ls='--')
                plt.legend()
            else:
                print('Plot already has average displayed.')
                
        plt.tight_layout()
