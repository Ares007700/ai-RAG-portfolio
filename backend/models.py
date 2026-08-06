#models.py works to define the structure of the database tables. It uses SQLAlchemy's ORM (Object Relational Mapper) to map Python classes to database tables. Each class represents a table, and each attribute of the class represents a column in that table. The models.py file is used by main.py to shape the data correctly when creating or querying items and users in the database.

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


#it will create a table called "items" with columns for id, name, and description. The id column is the primary key and is indexed for faster lookups. The name column is a string that cannot be null, while the description column is a string that can be null.
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String, nullable=True)


#it will create a table called "users" with columns for id, email, and hashed_password. The id column is the primary key and is indexed for faster lookups. The email column is a string that must be unique and is also indexed for faster lookups. The hashed_password column is a string that stores the hashed version of the user's password.
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


#it will create a table called "conversations" with columns for id, user_id, and created_at. The id column is the primary key and is indexed for faster lookups. The user_id column is a foreign key that references the id column in the users table, establishing a relationship between conversations and users. The created_at column is a datetime that defaults to the current UTC time when a new conversation is created.
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation")


#it will create a table called "messages" with columns for id, conversation_id, role, content, and created_at. The id column is the primary key and is indexed for faster lookups. The conversation_id column is a foreign key that references the id column in the conversations table, establishing a relationship between messages and conversations. The role column is a string that indicates whether the message was sent by the user or the assistant. The content column is a string that stores the actual message content. The created_at column is a datetime that defaults to the current UTC time when a new message is created.
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)       # "user" or "assistant"
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")