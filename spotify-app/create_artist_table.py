from sqlalchemy import inspect, create_engine, Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


conf ={
    'host':"spotify-db.c7g00umc0fcv.us-east-1.rds.amazonaws.com",
    'port':'5432',
    'database':"spotify-db",
    'user':"postgres",
    'password':"ILoveSpotify"
}

# create an engine that we can use to interact with our database
engine = create_engine("postgresql://{user}:{password}@{host}/{user}".format(**conf))

Base = declarative_base()

# Association table for many-to-many relationship between Artist and Album
artist_album_association = Table('artist_album_association', Base.metadata,
    Column('artist_id', String, ForeignKey('artists.artist_id')),
    Column('album_id', String, ForeignKey('albums.album_id'))
)

track_artists_association = Table('track_artists_association', Base.metadata,
    Column('track_id', String, ForeignKey('tracks.track_id')),
    Column('artist_id', String, ForeignKey('artists.artist_id'))
)

track_albums_association = Table('track_albums_association', Base.metadata,
    Column('track_id', String, ForeignKey('tracks.track_id')),
    Column('album_id', String, ForeignKey('albums.album_id'))
)


class Artists(Base):
    __tablename__ = 'artists'
    artist_id = Column(String, primary_key=True)
    followers = Column(Integer, nullable=True)
    genres = Column(JSONB, nullable=True)
    name = Column(String)
    popularity = Column(Integer, nullable=True)
    
    # related_artists = relationship('Artists',
    #                                secondary='artist_related_artists',
    #                                primaryjoin='Artists.artist_id==artist_related_artists.c.artist_id',
    #                                secondaryjoin='Artists.artist_id==artist_related_artists.c.related_artist_id',
    #                                backref='related_to')

    def __str__(self):
        return self.name

class Albums(Base):
    __tablename__ = 'albums'
    album_id = Column(String, primary_key=True)
    album_type = Column(String)
    total_tracks = Column(Integer)
    available_markets = Column(JSONB)
    images = Column(JSONB)
    album_name = Column(String)

    artists = relationship('Artists',
                           secondary=artist_album_association,
                           backref='albums')

    def __str__(self):
        return self.album_name

class Tracks(Base):
    __tablename__ = 'tracks'
    track_id = Column(String, primary_key=True)
    track_number = Column(Integer)
    key = Column(Integer)
    duration_ms = Column(Integer)
    instrumentalness = Column(Float)
    acousticness = Column(Float)
    danceability = Column(Float)
    energy = Column(Float)
    liveness = Column(Float)
    speechiness = Column(Float)
    valence = Column(Float)
    loudness = Column(Float)
    tempo = Column(Float)
    time_signature = Column(Integer)
    track_name = Column(String)

    artists = relationship('Artists',
                           secondary=track_artists_association,
                           backref='tracks')
    
    albums = relationship('Albums',
                          secondary=track_albums_association,
                          backref='tracks')

    def __str__(self):
        return self.track_name

# class User(Base):
#     __tablename__ = 'user'
#     user_id = Column(String, primary_key=True)
#     country = Column(String)
#     display_name = Column(String(255))
#     product = Column(String)

#     def __str__(self):
#         return self.display_name

# Drop tables
#Base.metadata.drop_all(engine)

# Create tables
#Base.metadata.create_all(engine)

# build an inspector
inspector = inspect(engine)

# use the inspector to find all the tables on the RDS
tables = inspector.get_table_names()

# take a look
print(tables)
