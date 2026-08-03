import unittest
from app import app, db

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        # Set up the test client and initialize the database
        self.app = app.test_client()
        self.app.testing = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_database.db'
        db.create_all()

    def tearDown(self):
        # Drop the database after each test
        db.session.remove()
        db.drop_all()

    def test_recommendation_route(self):
        # Simulate a POST request to the /recommendation route
        response = self.app.post('/recommendation', data=dict(
            Happy='Comedy',
            type_of_movies='Action'
        ), follow_redirects=True)

        # Check if the response is a redirection to /prediction (status code 200 OK for the final page)
        self.assertEqual(response.status_code, 200)
        # You can add more assertions here to check if the session variables are set correctly,
        # but that would require accessing the session outside of a request context, which is more complex.

if __name__ == '__main__':
    unittest.main()