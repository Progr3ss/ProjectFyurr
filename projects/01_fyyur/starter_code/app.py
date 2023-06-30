#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from flask_migrate import Migrate
from model import *

# App Config.
app = Flask(__name__)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://martinchibwe@localhost:5432/Fyyur'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
moment = Moment(app)
# db = SQLAlchemy(app)
db.init_app(app) 
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    # Query all venues
    venues = Venue.query.all()

    # Prepare data for rendering
    data = []
    for venue in venues:
        num_upcoming_shows =  len([show for show in venue.shows if show.start_time > datetime.now()])
        data.append({
            "city": venue.city,
            "state": venue.state,
            "venues": [{
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": num_upcoming_shows,
            }]
        })

    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Query the venue by ID
    venue = Venue.query.get(venue_id)
    
    # Prepare response data
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": ",".join(venue.genres) if venue.genres else "",
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0
    }
    
    # Get the past shows for the venue
    past_shows = Show.query.join(Artist).filter(
        Show.venue_id == venue_id,
        Show.start_time < datetime.now()
    ).all()
    
    # Get the upcoming shows for the venue
    upcoming_shows = Show.query.join(Artist).filter(
        Show.venue_id == venue_id,
        Show.start_time >= datetime.now()
    ).all()
    
    # Populate the past shows data
    for show in past_shows:
        data["past_shows"].append({
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        })
    
    # Populate the upcoming shows data
    for show in upcoming_shows:
        data["upcoming_shows"].append({
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        })
    
    # Update the show counts
    data["past_shows_count"] = len(past_shows)
    data["upcoming_shows_count"] = len(upcoming_shows)
    
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    if form.validate():
        try:
            venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website=form.website_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data,
                genres=','.join(form.genres.data) if form.genres.data else ""
            )
            db.session.add(venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        finally:
            db.session.close()
        return redirect(url_for('index'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error} for {getattr(form, field).label.text}")
        return redirect(url_for('create_venue_form'))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # Get the venue with the specified ID
    venue = Venue.query.get(venue_id)

    if not venue:
        # Venue with the specified ID does not exist
        flash('Venue not found.')
        return redirect(url_for('index'))

    try:
        # Delete the venue record from the database
        db.session.delete(venue)
        db.session.commit()
        flash('Venue deleted successfully.')
        return redirect(url_for('index'))
    except:
        # Handle exceptions if the session commit fails
        db.session.rollback()
        flash('An error occurred. Venue could not be deleted.')
        return redirect(url_for('index'))
    

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  #Query all artists
  artists = Artist.query.all()
  #load data 
  data = [] 
  for artist in artists:
     data.append({
        "id": artist.id,
        "name": artist.name,
     })

  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # Get the artist by their ID from the database
    artist = Artist.query.get(artist_id)

    # Prepare the response data dictionary
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.split(',') if artist.genres else [],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0,
    }

    # Get the artist's past shows
    past_shows = Show.query.join(Venue).filter(
        Show.artist_id == artist_id,
        Show.venue_id == Venue.id,
        Show.start_time < datetime.now()
    ).all()

    # Get the artist's upcoming shows
    upcoming_shows = Show.query.join(Venue).filter(
        Show.artist_id == artist_id,
        Show.venue_id == Venue.id,
        Show.start_time >= datetime.now()
    ).all()

    # Populate past shows data
    data['past_shows_count'] = len(past_shows)
    for show in past_shows:
        data['past_shows'].append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        })

    # Populate upcoming shows data
    data['upcoming_shows_count'] = len(upcoming_shows)
    for show in upcoming_shows:
        data['upcoming_shows'].append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        })

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    
    # Get the artist by their ID from the database
    artist = Artist.query.get(artist_id)
    
    # Populate the form fields with the artist's data
    form.name.data = artist.name
    form.genres.data = artist.genres.split(',') if artist.genres else []
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

 # Get the artist by their ID from the database
    artist = Artist.query.get(artist_id)

    # Update the artist's attributes with the form values
    artist.name = request.form['name']
    artist.genres = ','.join(request.form.getlist('genres'))
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.website = request.form['website']
    artist.facebook_link = request.form['facebook_link']
    artist.seeking_venue = 'seeking_venue' in request.form
    artist.seeking_description = request.form['seeking_description']
    artist.image_link = request.form['image_link']

    # Commit the changes to the database
    try:
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    
    # Retrieve the venue with the given ID from the database
    venue = Venue.query.get(venue_id)
    
    if venue:
        # Populate the form with the venue data
        form.name.data = venue.name
        form.genres.data = venue.genres
        form.address.data = venue.address
        form.city.data = venue.city
        form.state.data = venue.state
        form.phone.data = venue.phone
        form.website_link.data = venue.website
        form.facebook_link.data = venue.facebook_link
        form.seeking_talent.data = venue.seeking_talent
        form.seeking_description.data = venue.seeking_description
        form.image_link.data = venue.image_link
    
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()

    try:
        # Retrieve the venue with the given ID from the database
        venue = Venue.query.get(venue_id)

        if venue:
            # Update the venue record with the new attribute values from the form
            venue.name = form.name.data
            venue.genres = ",".join(form.genres.data)  # Convert genres to a string
            venue.address = form.address.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.phone = form.phone.data
            venue.website = form.website_link.data
            venue.facebook_link = form.facebook_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data
            venue.image_link = form.image_link.data

            # Commit the changes to the database
            db.session.commit()
            flash('Venue ' + venue.name + ' was successfully updated!')
        else:
            flash('An error occurred. Venue ID ' + str(venue_id) + ' does not exist.')
    except Exception as e:
        # Handle any exceptions that may occur during the update process
        db.session.rollback()
        flash('An error occurred. Venue could not be updated.')
        print(str(e))
    finally:
        # Close the database session
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  # flash('Artist ' + request.form['name'] + ' was successfully listed!')

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  # return render_template('pages/home.html')
    form = ArtistForm(request.form)
    if form.validate():
        try:
            artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                image_link=form.image_link.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                website=form.website_link.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data
            )
            db.session.add(artist)
            db.session.commit()
            # on successful db insert, flash success
            flash('Artist ' + artist.name + ' was successfully listed!')
            return render_template('pages/home.html')
        except:
            db.session.rollback()
            # TODO: on unsuccessful db insert, flash an error instead.
            # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
            flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
            return render_template('forms/new_artist.html', form=form)
        finally:
            db.session.close()
    else:
        flash('An error occurred. Please check your input.')
        return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
    shows = Show.query.join(Artist).join(Venue).all()

    # Prepare response data
    data = []
    for show in shows:
        data.append({
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    #   # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    # called to create new shows in the db, upon submitting new show listing form
    # Get the form data
    form = ShowForm(request.form)

    # Create a new Show record
    show = Show(
        artist_id=form.artist_id.data,
        venue_id=form.venue_id.data,
        start_time=form.start_time.data
    )

    try:
        # Add the new show to the database
        db.session.add(show)
        db.session.commit()

        # on successful db insert, flash success
        flash('Show was successfully listed!')
        return render_template('pages/home.html')
    except:
        # on unsuccessful db insert, flash an error
        flash('An error occurred. Show could not be listed.')
        db.session.rollback()
        return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
