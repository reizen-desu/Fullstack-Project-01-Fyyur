import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category


# Functions

"""Paginate function
Used to paginate questions. Used to handle display of
questions per page. QUESTIONS_PER_PAGE defines the
number of questions shown per page.
"""

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    current_questions = []

    page = request.args.get('page', 1, type=int)
    start = (page-1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    cors = CORS(app, resources={r"*": {"origins": '*'}})

    # Using the after_request decorator to set Access-Control-Allow
    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Headers",
                             "Content-Type, Authorization, true")
        response.headers.add(
            "Access-Control-Allow-Headers", "GET, POST, DELETE")
        return response

    # Endpoint to handle GET requests for all available categories
    @app.route('/categories')
    def get_categories():

        categories = Category.query.order_by(Category.id).all()
        categories_dict = {}

        for category in categories:
            categories_dict[category.id] = category.type

        if len(categories_dict) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': categories_dict
        })

    # This endpoint returns a list of questions and its adta
    @app.route('/questions')
    def get_questions():

        # Used for pagination | get all questions and paginate
        selection = Question.query.order_by(Question.id).all()
        questions_paginated = paginate_questions(request, selection)

        # If no questions are returned then return not found
        if len(questions_paginated) == 0:
            abort(404)

        # Add categories data to dict
        categories = Category.query.order_by(Category.id).all()
        categories_dict = {}
        for category in categories:
            categories_dict[category.id] = category.type

        return jsonify({
            'success': True,
            'questions': questions_paginated,
            'total_questions': len(selection),
            'categories': categories_dict
        })

    # Deletes a question by question ID
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })
        except:
            abort(422)

    # Creates a new question with the data that the user enters
    @app.route('/questions', methods=['POST'])
    def post_question():
        body = request.get_json()

        new_question = body.get('question')
        new_answer = body.get('answer')
        new_difficulty = body.get('difficulty')
        new_category = body.get('category')

        try:
            question = Question(question=new_question, answer=new_answer,
                                difficulty=new_difficulty, category=new_category)
            question.insert()

            return jsonify({
                'success': True
            })
        except:
            abort(422)

    # Returns a list of questions based in the search term
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()
        search_term = body.get('searchTerm', None)

        if search_term:
            search_results = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()

            return jsonify({
                'success': True,
                'questions': [question.format() for question in search_results],
                'total_questions': len(search_results),
            })
        abort(404)

    # Get list of questions based on a given category
    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):

        category = Category.query.get(category_id)
        selection = Question.query.order_by(Question.id).filter(
            Question.category == category_id).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(current_questions),
            'current_category': category_id

        })

    @app.route('/quizzes', methods=['POST'])
    def get_questions_for_quiz():

        # Get data from JSON
        body = request.get_json()

        try:
            previous_questions = body.get('previous_questions')
            quiz_category = body.get('quiz_category')['id']

            questions = []
            if quiz_category == 0:
                questions = Question.query.filter(
                    Question.id.notin_(previous_questions)).all()
            else:
                category = Category.query.get(quiz_category)
                questions = Question.query.filter(Question.id.notin_(
                    previous_questions), Question.category == quiz_category).all()

            current_question = None

            # if there's more than one question, randomizes it
            if (len(questions) > 0):
                pointer = random.randrange(0, len(questions))
                current_question = questions[pointer].format()

            return jsonify({
                'success': True,
                'question': current_question,
                'total_questions': len(questions)
            })

        except:
            abort(400)

    '''
    ERROR HANDLERS
  '''

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'Bad request'
        }), 400

    @app.errorhandler(404)
    def page_not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': "Resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable_resource(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': "Unprocessable resource"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': "Internal server error"
        }), 500

    return app
