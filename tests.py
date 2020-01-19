import unittest, requests, json

class TestAPI(unittest.TestCase):

    # Calls registration endpoint with username Foo and checks its presence in the user list
    def test_create(self):
        requests.post("http://127.0.0.1:5000/api/auth/register", json={"username":"Foo"})
        user_list = json.loads(requests.get("http://127.0.0.1:5000/api/users/list").text)["user_list"]
        self.assertTrue("Foo" in user_list)

    # Calls delete endpoint with username Bar and checks its absence in the user list
    def test_delete(self):
        requests.delete("http://127.0.0.1:5000/api/users/delete", json={"username":"Bar"})
        user_list = json.loads(requests.get("http://127.0.0.1:5000/api/users/list").text)["user_list"]
        self.assertFalse("Bar" in user_list)

    # Iterates over returned list from user list endpoint and asserts that calling the login endpoint on each user returns an access token
    def test_list(self):
        user_list = json.loads(requests.get("http://127.0.0.1:5000/api/users/list").text)["user_list"]
        for users in user_list:
            self.assertFalse(json.loads(requests.post("http://127.0.0.1:5000/api/auth/login", json={"username":users}).text).get("access_token", None)==None)


if __name__ == '__main__':
    unittest.main()
