#The request arrives at main.py first — that's the "front door." It hits the create_item function.
#It uses database.py's setup to open a connection (get a db session) — this is the "how do I even talk to the database" part.
#It uses models.py's Item blueprint to shape the data correctly — this is the "what does a valid row look like" part.
#It saves that shaped data through the open connection (db.add, db.commit).
#Response goes back.


from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from fastapi import HTTPException

from database import engine, SessionLocal, Base
import models

from passlib.context import CryptContext

from jose import jwt
from datetime import datetime, timedelta

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from jose import JWTError

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()  # ← this line actually reads .env into memory

from fastapi.responses import StreamingResponse


Base.metadata.create_all(bind=engine)  # creates the table if it doesn't exist

app = FastAPI()

# Dependency: gives each request its own DB session, closes it after
def get_db():
    db = SessionLocal()
    try:
        yield db #it will yield the db session to the request, and then close it after the request is done. This is important because we don't want to keep the db session open for too long, as it can cause issues with the database connection pool.
    finally:
        db.close()

# Pydantic model for input
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None  #it will allow the description to be optional, so that we can create an item without a description. If the description is not provided, it will be set to None.

#Create an item in the database, return the created item
@app.post("/items")
def create_item(payload: ItemCreate, db: Session = Depends(get_db)): #it will create a new item in the database, and return the created item. It will use the ItemCreate model to validate the input data, and it will use the get_db dependency to get a db session.
    item = models.Item(name=payload.name, description=payload.description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

#get all items from the database, return a list of items
@app.get("/items")
def list_items(db: Session = Depends(get_db)): #it will get all the items from the database, and return a list of items. It will use the get_db dependency to get a db session.
    return db.query(models.Item).all()

#search for an item by id, if not found, return 404
@app.get("/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

#delete an item by id, if not found, return 404
@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": f"Item {item_id} deleted"}




#Update an item by id, if not found, return 404
class ItemUpdate(BaseModel):
    name: str
    description: Optional[str] = None

#for PATCH, we can use the same ItemUpdate model, but we will only update the fields that are provided in the request. 
# If a field is not provided, we will leave it unchanged.
@app.patch("/items/{item_id}")
def patch_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    item.name = payload.name
    item.description = payload.description

    db.commit()
    db.refresh(item)
    return item




#for user signup, we will create a new user in the database with a hashed password. 
# We will use the passlib library to hash the password.
class UserCreate(BaseModel):
    email: str
    password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") #it will use bcrypt to hash the password, and will automatically handle the salt for us.

#it will check if the email is already registered, if it is, it will return a 400 error.
@app.post("/signup")
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = pwd_context.hash(payload.password) #it will hash the password using bcrypt, and will automatically handle the salt for us.
    user = models.User(email=payload.email, hashed_password=hashed_pw) #it will create a new user with the hashed password
    db.add(user) #it will add the new user to the database
    db.commit() #it will commit the transaction to the database
    db.refresh(user) #it will refresh the user object with the data from the database, so that we can return the id and email of the new user.
    return {"id": user.id, "email": user.email} #it will return the id and email of the new user, but not the password, because we don't want to expose the password to the client.





#it will check if the email and password are correct, if they are, it will return a success message. If they are not, it will return a 401 error.
class UserLogin(BaseModel):
    email: str
    password: str

#@app.post("/login")   --------->   this is without token version, it will just check if the email and password are correct, and return a success message if they are. If they are not, it will return a 401 error.
#def login(payload: UserLogin, db: Session = Depends(get_db)):  #it will check the user's credentials
    #user = db.query(models.User).filter(models.User.email == payload.email).first() #it will query the database for a user with the provided email. If no user is found, it will return None.

    #if user is None:
        #raise HTTPException(status_code=401, detail="Invalid email or password")

    #if not pwd_context.verify(payload.password, user.hashed_password): #it will verify the provided password against the hashed password stored in the database. If the password is incorrect, it will return False.
        #raise HTTPException(status_code=401, detail="Invalid email or password")

    #return {"message": "Login successful"}



#Create a token when login succeeds
SECRET_KEY = "change-this-to-something-random-and-long"  #key used to sign the JWT token. In a real application, you should use a more secure key, such as a randomly generated string of at least 32 characters. You should also keep this key secret and not hard-code it in your code. Instead, you can store it in an environment variable or a configuration file.
ALGORITHM = "HS256"   #algorithm used to sign the JWT token. HS256 is a symmetric algorithm, which means that the same key is used for both signing and verifying the token. In a real application, you should use a more secure algorithm, such as RS256, which uses asymmetric keys.

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)):  #it will create a JWT token with the provided data and expiration time. The default expiration time is 30 minutes, but you can change it by passing a different expires_delta value to the function.
    to_encode = data.copy()  #it will create a copy of the data dictionary, so that we don't modify the original data. This is important because we want to keep the original data intact, in case we need to use it later.
    expire = datetime.utcnow() + expires_delta   #it will calculate the expiration time by adding the expires_delta to the current UTC time. This is important because we want the token to expire after a certain amount of time, so that it can't be used indefinitely.
    to_encode.update({"exp": expire}) #it will add the expiration time to the data dictionary, so that we can include it in the JWT token. This is important because we want the token to have an expiration time, so that it can't be used indefinitely.
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) #it will encode the data dictionary into a JWT token using the SECRET_KEY and ALGORITHM. This is important because we want to create a secure token that can be used to authenticate the user.


#Return a token from /login   version with token, it will return a token if the email and password are correct. If they are not, it will return a 401 error.
@app.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):   #it will check the user's credentials and return a JWT token if they are correct. If they are not, it will return a 401 error.
    user = db.query(models.User).filter(models.User.email == payload.email).first()    #it will query the database for a user with the provided email.

    if user is None or not pwd_context.verify(payload.password, user.hashed_password):  #it will check if the user exists and if the password is correct. If either of these checks fail, it will raise an HTTPException with a 401 status code and a detail message indicating that the email or password is invalid.
        raise HTTPException(status_code=401, detail="Invalid email or password")  #it will raise an HTTPException with a 401 status code and a detail message indicating that the email or password is invalid.

    token = create_access_token({"sub": user.email})   #it will create a JWT token with the user's email as the subject. The token will expire in 30 minutes by default, but this can be changed by passing a different expires_delta value to the create_access_token function.
    return {"access_token": token, "token_type": "bearer"}  #it will return a JSON response with the access token and the token type. The access token can be used to authenticate the user in subsequent requests, and the token type indicates that the token is a bearer token, which means that it should be included in the Authorization header of the request.


#A protected route — only works with a valid token
#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")   #it will create an OAuth2PasswordBearer instance that will be used to extract the token from the Authorization header of the request. The tokenUrl parameter specifies the URL where the client can obtain a token, which in this case is the /login endpoint.

security = HTTPBearer()  #it will create an HTTPBearer instance that will be used to extract the token from the Authorization header of the request. The HTTPBearer class is a subclass of the OAuth2PasswordBearer class, and it provides a simpler way to extract the token from the request.
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),  #it will use the HTTPBearer instance to extract the token from the Authorization header of the request. The credentials parameter will contain the extracted token, which can be used to authenticate the user.
    db: Session = Depends(get_db)  #it will use the get_db dependency to get a db session, which will be used to query the database for the user associated with the token.
):
    token = credentials.credentials  # this pulls out just the raw token string
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  #it will decode the JWT token using the SECRET_KEY and ALGORITHM. If the token is invalid or expired, it will raise a JWTError exception, which will be caught by the except block below.
        email = payload.get("sub")  #it will extract the email from the payload of the decoded token. The email is stored in the "sub" claim of the token, which is a standard claim used to identify the subject of the token. If the email is not found in the payload, it will raise an HTTPException with a 401 status code and a detail message indicating that the token is invalid or expired.
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc 

    user = db.query(models.User).filter(models.User.email == email).first()  #it will query the database for a user with the extracted email. If no user is found, it will return None, which will be checked in the next line. If a user is found, it will return the user object, which can be used to access the user's id and email in the read_me endpoint below.
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

@app.get("/me")  #it will return the current user's id and email if the token is valid. If the token is invalid or expired, it will raise an HTTPException with a 401 status code and a detail message indicating that the token is invalid or expired.
def read_me(current_user: models.User = Depends(get_current_user)):   #it will use the get_current_user dependency to get the current user object associated with the token. If the token is invalid or expired, it will raise an HTTPException with a 401 status code and a detail message indicating that the token is invalid or expired.
    return {"id": current_user.id, "email": current_user.email}    #it will return a dictionary containing the id and email of the current user.


#for the OpenRouter API, we will use the openai library to send requests to the OpenRouter API. We will create a new endpoint /chat that will accept a message from the user, send it to the OpenRouter API, and return the response from the API.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = os.getenv("OPENROUTER_URL")

client = OpenAI(    #it will create an OpenAI client instance that will be used to send requests to the OpenRouter API. The client will use the OPENROUTER_API_KEY environment variable to authenticate the requests, and it will use the base_url parameter to specify the base URL of the OpenRouter API.
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_URL,
)

class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


@app.post("/chat")
def chat(
    payload: ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Get existing conversation, or create a new one
    if payload.conversation_id:
        conversation = db.query(models.Conversation).filter(
            models.Conversation.id == payload.conversation_id,
            models.Conversation.user_id == current_user.id
        ).first()
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = models.Conversation(user_id=current_user.id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 2. Save the user's new message
    user_message = models.Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.message
    )
    db.add(user_message)
    db.commit()

    # 3. Load history, same as before
    history = db.query(models.Message).filter(
        models.Message.conversation_id == conversation.id
    ).order_by(models.Message.id).all()

    ai_messages = [{"role": m.role, "content": m.content} for m in history]

    # 4. This function does the actual streaming, piece by piece
    def generate():
        full_reply = ""
        # Send the conversation_id first, on its own line, with a marker
        yield f"__CONVO_ID__:{conversation.id}\n"

        error_note = None
        try:
            stream = client.chat.completions.create(
                model=os.getenv("OPENROUTER_MODEL"),
                messages=ai_messages,
                stream=True
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_reply += delta
                    yield delta

            assistant_message = models.Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_reply
            )
            db.add(assistant_message)
            db.commit()

        except (AttributeError, ValueError, KeyError):
            error_note = "[Error: response interrupted]"

        if error_note is not None:
            assistant_message = models.Message(
                conversation_id=conversation.id,
                role="assistant",
                content=error_note
            )
            db.add(assistant_message)
            db.commit()
            yield "\n\n⚠️ Something went wrong. Please try again."

    return StreamingResponse(generate(), media_type="text/plain")


@app.get("/conversations")
def list_conversations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversations = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id
    ).order_by(models.Conversation.created_at.desc()).all()

    result = []
    for convo in conversations:
        first_message = db.query(models.Message).filter(
            models.Message.conversation_id == convo.id
        ).order_by(models.Message.id).first()

        result.append({
            "id": convo.id,
            "created_at": convo.created_at,
            "preview": first_message.content if first_message else "(empty)"
        })

    return result

@app.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.id).all()

    return [{"role": m.role, "content": m.content} for m in messages]








#person.age         age value stored inside person
#person.walk()      hey person run your walk() method


#thing.something
#means: "go inside thing, and give me something."
#If something is a plain value → you're reading/writing data (item.name)
#If something is followed by () → you're calling a function that belongs to that object (db.commit())