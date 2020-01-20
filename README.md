# Betterfin Demo
## Fetching New Transactions
To keep the database updated with new transactions, I would set up an endpoint on the backend called /webhooks to accept POST requests (webhooks) from Plaid. When a transaction webhook is sent to /webhooks with the code "DEFAULT_UPDATE", the backend would call /transactions/get from Plaid and fetch however many transactions is specified by the transaction webhook field "new_transactions". These would then be saved in the database. To safeguard against duplicate transactions I would set a uniqueness constraint on the field "transaction_id" in the database.

## Endpoints
### Authentication
#### POST 		/api/auth/login
Requires string username to log in as a user. If successful, returns a JWT. Store this client-side and use with an authorization header for permission-restricted endpoints. Errors will return if the user is not provided or doesn't exist. 
##### Sample Payload
```
{ 
    username: "Foo" 
}
```
##### Sample Response
```
{ 
    access_token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1Nzk0NjAxMjMsIm5iZiI6MTU3OTQ2MDEyMywianRpIjoiYWVhYWZhYTAtMTIxZS00MmE4LWIwNTYtZGUwMjVhNDI0ZjA4IiwiZXhwIjoxNTc5NDYxMDIzLCJpZGVudGl0eSI6InRlc3QiLCJmcmVzaCI6ZmFsc2UsInR5cGUiOiJhY2Nlc3MifQ.2JxhEK8XDZAAJyyBu5VQX_Qg7RARIaSuF9im38I_50o" 
}
```
#### DELETE	/api/auth/logout 	
Called with an authorization header to put user's JWT on an in-memory blacklist. Will return an error if token is invalid
##### Sample Header
```
{
    "Authorization": "JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1Nzk0NjAxMjMsIm5iZiI6MTU3OTQ2MDEyMywianRpIjoiYWVhYWZhYTAtMTIxZS00MmE4LWIwNTYtZGUwMjVhNDI0ZjA4IiwiZXhwIjoxNTc5NDYxMDIzLCJpZGVudGl0eSI6InRlc3QiLCJmcmVzaCI6ZmFsc2UsInR5cGUiOiJhY2Nlc3MifQ.2JxhEK8XDZAAJyyBu5VQX_Qg7RARIaSuF9im38I_50o"
}
```
##### Sample Response
```
{
  "msg": "Logged out"
}
```
#### POST		/api/auth/register
Requires string username to sign up. Errors will return if username is not provided or if user by the requested name already exists.
##### Sample Payload
``` 
{ 
    username: "Foo" 
} 
 ```
##### Sample Response
```
{
  "msg": "Logged out"
}
```

### Users
#### GET		/api/users/list
Retrieves a list of current usernames. 
##### Sample Response:
```
{
  "user_list": [
    "test1",
    "test2"
  ]
}
```
#### DELETE 	        /api/users/delete
Deletes user with provided username from database. If user with provided username does not exist, an error is returned.
##### Sample Payload
```
{ 
    username: "Foo" 
} 
```
##### Sample Response
```
{
  "msg": "User deleted"
}
```
### Banking
#### POST 		/api/banking/takeToken
Call this endpoint inside the onSuccess callback in Plaid Link to send public token to backend. Backend will exchange tokens with Plaid to receive an access_token and item_id, which is associated with the user in the database.
##### Sample Request
```
{
    public_token: "public-sandbox-350d3115-f50a-4839-9029-fb6ef9152a86"
}
```
##### Sample Response
```
{
  "msg": "Tokens exchanged"
}
```
#### GET 		/api/banking/balance
Returns accounts and their current balances where user has access_token stored, otherwise returns an error.
##### Sample Header
```
{ "Authorization": "JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1Nzk0NjAxMjMsIm5iZiI6MTU3OTQ2MDEyMywianRpIjoiYWVhYWZhYTAtMTIxZS00MmE4LWIwNTYtZGUwMjVhNDI0ZjA4IiwiZXhwIjoxNTc5NDYxMDIzLCJpZGVudGl0eSI6InRlc3QiLCJmcmVzaCI6ZmFsc2UsInR5cGUiOiJhY2Nlc3MifQ.2JxhEK8XDZAAJyyBu5VQX_Qg7RARIaSuF9im38I_50o" }
```
##### Sample Response
```
{
  "balances": [
    {
      "account_id": "vnrD1VWBl5uXLnJXwaEQfNMyNVMKNMFWjrDLk", 
      "current_balance": 110
    }, 
    {
      "account_id": "RDeMEgyBGVC6gw46LWQkcqj8qej6qjcRK8Q64", 
      "current_balance": 210
    }, 
    {
      "account_id": "6Ew6VWbXvmUPNn9PGVBzHR7oR97BR7fgW4REe", 
      "current_balance": 1000
    }, 
    {
      "account_id": "XWNGmnVor1SdyRJdkebvhXgVXGgxXgCd4GR7v", 
      "current_balance": 410
    }, 
    {
      "account_id": "DDrqNazoBRCxy3vxnkEMcPeaP5eZPeivgb8AN", 
      "current_balance": 43200
    }, 
    {
      "account_id": "VDXLnAypq1CjE7pjvJykuVkwVDk4VktW4zJjy", 
      "current_balance": 320.76
    }, 
    {
      "account_id": "wmzlLVX3qAFgNwMgBPGkCJbGJwbQJburvJ64Z", 
      "current_balance": 23631.9805
    }, 
    {
      "account_id": "5mwbDEM75xFlx5MlQoRrFDdPD3dEDdfZo9Dar", 
      "current_balance": 65262
    }
  ]
}
```
#### POST 		/api/banking/transactions/save
Saves complete transaction history from Plaid to database where user has access_token stored, otherwise returns an error.
##### Sample Header
```
{
    "Authorization": "JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1Nzk0NjAxMjMsIm5iZiI6MTU3OTQ2MDEyMywianRpIjoiYWVhYWZhYTAtMTIxZS00MmE4LWIwNTYtZGUwMjVhNDI0ZjA4IiwiZXhwIjoxNTc5NDYxMDIzLCJpZGVudGl0eSI6InRlc3QiLCJmcmVzaCI6ZmFsc2UsInR5cGUiOiJhY2Nlc3MifQ.2JxhEK8XDZAAJyyBu5VQX_Qg7RARIaSuF9im38I_50o"
}
```
##### Sample Response
```
{
   msg: "Transactions saved."
}
```
#### GET 		/api/banking/transactions/stats
Returns statistics on amounts by transaction category where user has transactions stored. Otherwise, returns error. Includes average, median, most frequent element and highest/lowest element.
##### Sample Header
```
{
    "Authorization": "JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1Nzk0NjAxMjMsIm5iZiI6MTU3OTQ2MDEyMywianRpIjoiYWVhYWZhYTAtMTIxZS00MmE4LWIwNTYtZGUwMjVhNDI0ZjA4IiwiZXhwIjoxNTc5NDYxMDIzLCJpZGVudGl0eSI6InRlc3QiLCJmcmVzaCI6ZmFsc2UsInR5cGUiOiJhY2Nlc3MifQ.2JxhEK8XDZAAJyyBu5VQX_Qg7RARIaSuF9im38I_50o"
}
```
##### Sample Response
```
{
    Airlines and Aviation Services: {avg: -10.204081632653061, freq: -500, max: 500, median: -500, min: -500}
    Car Service: {avg: 5.855510204081633, freq: 5.4, max: 6.33, median: 5.4, min: 5.4}
    Coffee Shop: {avg: 4.33, freq: 4.33, max: 4.33, median: 4.33, min: 4.33}
    Credit: {avg: -4.22, freq: -4.22, max: -4.22, median: -4.22, min: -4.22}
    Credit Card: {avg: 25, freq: 25, max: 25, median: 25, min: 25}
    Debit: {avg: 5850, freq: 5850, max: 5850, median: 5850, min: 5850}
    Deposit: {avg: 1000, freq: 1000, max: 1000, median: 1000, min: 1000}
    Food and Drink: {avg: 216.6117886178862, freq: 500, max: 500, median: 89.4, min: 4.33}
    Gyms and Fitness Centers: {avg: 78.5, freq: 78.5, max: 78.5, median: 78.5, min: 78.5}
}
```
#### POST 		/api/banking/transactions/filtered
When user has transactions stored on the database, returns transactions by specified filters in payload. Otherwise, returns error. Filters include
- startDate, endDate, exactDate: Searches for transaction dates on or after startDate, on or before endDate, and exactly on exactDate. Dates are formatted YYYY-MM-DD
- lowerBound, upperBound, exactAmount: Inclusive range and exact quantity for transaction amount
- categories: Takes a list of categories
##### Sample Header
```
{
    "Authorization": "JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1Nzk0NjAxMjMsIm5iZiI6MTU3OTQ2MDEyMywianRpIjoiYWVhYWZhYTAtMTIxZS00MmE4LWIwNTYtZGUwMjVhNDI0ZjA4IiwiZXhwIjoxNTc5NDYxMDIzLCJpZGVudGl0eSI6InRlc3QiLCJmcmVzaCI6ZmFsc2UsInR5cGUiOiJhY2Nlc3MifQ.2JxhEK8XDZAAJyyBu5VQX_Qg7RARIaSuF9im38I_50o"
}
```
##### Sample Payload
```
{
    "startDate": "2019-01-01" , 
    "endDate": "2019-01-31", 
    "categories": ["Travel", "Ride Share"]
}
```

##### Sample Response
```
{
    transactions: [{
    _id: "5e24ba8647162a9f87a09928",
    account_id: "pQBnVGGqL8C5AyGzybPmCqjlJ8G4p6HL4a8lG",
    account_owner: null,
    amount: 5.4,
    authorized_date: null,
    category: ["Travel", "Car Service", "Ride Share"],
    category_id: "22006001",
    date: "2019-01-21",
    iso_currency_code: "USD",
    location: {address: null, city: null, country: null, lat: null, lon: null, postal_code: null, region: null,…},
    name: "Uber 063015 SF**POOL**",
    payment_channel: "online",
    payment_meta: {by_order_of: null, payee: null, payer: null, payment_method: null, payment_processor: null,…},
    pending: false,
    pending_transaction_id: null,
    transaction_id: "G4MDP11W3aiAlJX5JarpFG9anNPPG7T1lkRv5",
    transaction_type: "special",
    unofficial_currency_code: null,
    username: "new1"},
    
    {_id: "5e24ba8747162a9f87a09932",
    account_id: "pQBnVGGqL8C5AyGzybPmCqjlJ8G4p6HL4a8lG",
    account_owner: null,
    amount: 6.33,
    authorized_date: null,
    category: ["Travel", "Car Service", "Ride Share"],
    category_id: "22006001",
    date: "2019-01-04",
    iso_currency_code: "USD",
    location: {address: null, city: null, country: null, lat: null, lon: null, postal_code: null, region: null,…},
    name: "Uber 072515 SF**POOL**",
    payment_channel: "online",
    payment_meta: {by_order_of: null, payee: null, payer: null, payment_method: null, payment_processor: null,…},
    pending: false,
    pending_transaction_id: null,
    transaction_id: "gxgWV11EAeuoALBeLGR6i3woMlPP3WHgbWdB7",
    transaction_type: "special",
    unofficial_currency_code: null,
    username: "new1"}]
}
```


