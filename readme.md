**Points API**
----
**Installation**

  The Points API uses Python 3.8, Flask, and Flask_RESTful.
  To install and run the service, please follow these steps
  1. Download and install Python 3.8 for your respective platform
     1. Instructions in the following link: https://realpython.com/installing-python/ should help clear up any issues and properly install python
  2. After having installed Python, use pip to install the requirements
     1. Navigate to the Points app directory using your terminal of choice
     2. Type in `pip install -r requirements.txt` and press enter
     3. This should install all requisite python packages
     4. If there are any issues, install each component manually
        1. Open the requirements.txt file
        2. For each line in the file, type into your terminal the following: `pip install \<library\>==\<version\>` and press enter
  3. Type into your terminal the following command: `flask run` and press enter
  4. The terminal will output something like the following: 
        ``` * Environment: production
        WARNING: This is a development server. Do not use it in a production deployment.
        Use a production WSGI server instead.
        * Debug mode: off
        * Running on http://x.x.x.x:5000/ (Press CTRL+C to quit)"
        ```
  5. Copy the url on the last line
  6. This is the root url for the app
  7. You can use any method you like to send requests to the service
  8. One free and easy way to test development apps like this is to use Postman


**Background**

Our users have points in their accounts. Users only see a single balance in their accounts. But for reporting purposes we actually track their
points per payer/partner. In our system, each transaction record contains: payer (string), points (integer), timestamp (date).

For earning points it is easy to assign a payer, we know which actions earned the points. And thus which partner should be paying for the points.

When a user spends points, they don't know or care which payer the points come from. But, our accounting team does care how the points are
spent. There are two rules for determining what points to "spend" first:

● We want the oldest points to be spent first (oldest based on transaction timestamp, not the order they’re received)

● We want no payer's points to go negative.


**Endpoints**

The Points API uses two endpoints to accomplish this

1. **Transactions**

The transactions endpoint uses only the `POST` method to add transactions to an in-memory store.

* **URL**
  
  `"/users"`

* **Method:**
  `POST`:

  The `POST` request for the transactions endpoint allows users to add transactions to the in-memory store of transactions.

  Each transaction contains a payer, the number of points (can be positive or negative), and the transaction timestamp.

  If succesful, it responds with a `209 Created`

  If not, it responds with a `409 Conflict`

  The request body can either be JSON or raw text formatted as JSON

  **Request Body**

  `{"payer": \<payer\>, "points": \<points\>, "timestamp": \<timestamp\>}`

  The timestamp format is `YYYY-MM-DD`T`HH:MM:SS`Z

* **Success Response:**
  

  * **Code:** 200 
 
* **Error Response:**

  * **Code:** 409 <br />

* **Sample Body:**

   `{ "payer": "DANNON", "points": 1000, "timestamp": "2020-11-02T14:00:00Z" }`
* **Sample Response:**
   `200`



* **Notes:**

  Multiple transactions can be added sequentially through multiple calls. 

1. **Points**

The Points endpoint manages a user's points. It retrieves the total points that the user has from each vendor using the `GET`  request and can spend points with the aforementioned criteria using the `POST` request.

* **URL**
  
  `"/points"`

* **Method:**
  1. `GET`:

  The `GET` request for the points endpoint allows users to retreive all payer point balances for the user.

  If succesful, it responds with a JSON-formatted text body that contains point balances.

  The request body can either be JSON or raw text formatted as JSON

  **Request Body**

  `None`


* **Success Response:**
  ```
  {
      "\<payer1\>": \<points\>,
      "\<payer2\>": \<points\>,
      ...

  }
  ```
 
* **Error Response:**

  * **Code:** 404 <br />

* **Sample Body:**

   `None`
* **Sample Response:**
   ```
    {
        "DANNON": 1000,
        "UNILEVER": 0,
        "MILLER COORS": 5300
    }
   ```

* **Notes:**

  None. 

1. `POST`:

  The `POST` request for the points endpoint allows users to spend points using the aforementioned criteria.

  The request body supplies the number of points to be spent. 

  If succesful, it responds with a list that contains an item for each payer that includes the number of points to be subtracted from the payer's point balance.

  If not, it responds with a `400 Bad Request`

  The request body can either be JSON or raw text formatted as JSON

  **Request Body**

  `{"points": \<points\>}`


* **Success Response:**
  
    ```
    [
        {"payer": "\<payer1\>", "points": -"\<points\>"},
        {"payer": "\<payer2\>", "points": -"\<points\>"},
        ...
    ]
    ```

 
* **Error Response:**

  * **Code:** 400 <br />

* **Sample Body:**

   `{ "points": 5000 }`
* **Sample Response:**
  
    ```
    [
        {"payer": "DANNON"", "points": -100},
        {"payer": "UNILEVER", "points": -200},
        {"payer": "MILLER COORS", "points": -4700},
        ...
    ]
    ```
   

* **Notes:**
    Assumes adding transactions will never make points negative.

    Assumes first transaction cannot be negative.
    
    Past transactions will be considered complete and not a sample.

    Known issues: 
    1. Sometimes, adding transactions after having spent points results in negative point balances. User should add all requisite transactions first and then spending points.

    2. Spent points will not be reflected in transactions but will be reflected in point balances.


  