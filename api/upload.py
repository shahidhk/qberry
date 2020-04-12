import requests
import csv
import os
import io
from flask import Flask, Response, request, render_template_string

app = Flask(__name__)

endpoint = os.getenv('HASURA_ENDPOINT')
admin_secret = os.getenv('HASURA_ADMIN_SECRET')
admin_password = os.getenv('ADMIN_PASSWORD')

form_html = """
<html>
  <head>
    <title>Qberry Admin | Upload questions</title>
  </head>
  <body>
    <h1>Qberry Admin | Upload Questions</h1>
    <form method="POST" enctype="multipart/form-data">
      <table>
      <tr>
        <td><label for="password">Password:</label></td>
        <td><input type="password" id="password" name="password" required></td>
      </tr>

      <tr>
        <td><label for="quiz_name">Quiz name:</label></td>
        <td><input type="text" id="quiz_name" name="quiz_name" required></td>
      </tr>

      <tr>
        <td><label for="start_date">Start date:</label></td>
        <td><input type="date" id="start_date" name="start_date" required></td>
        <td><label for="start_time">Start time:</label></td>
        <td><input type="time" id="start_time" name="start_time" required></td>
      </tr>

      <tr>
        <td><label for="end_date">End date:</label></td>
        <td><input type="date" id="end_date" name="end_date" required></td>
        <td><label for="end_time">End time:</label></td>
        <td><input type="time" id="end_time" name="end_time" required></td>
      </tr>

      <tr>
        <td><label for="qs_file">
          Questions CSV (<a href="/quiz_questions_format.csv">format sample</a>)
         </label></td>
        <td><input type="file" id="qs_file" name="qs_file" required></td>
      </tr>

      <tr>
        <td>
          <input name="sumbit" type="submit" value="Submit" />
          <input name="reset" type="reset" value="Reset" />
        </td>
      </tr>

    </form>
  </body>
</html>
"""

quiz_template = """
<html>
  <head>
    <title>Qberry Admin | Quiz Uploaded</title>
  </head>
  <body>
    <h1>Questions uploaded!</h1>
    <table>
      <tr><td>ID:</td><td>{{ quiz.id}}</td></tr>
      <tr><td>Name:</td><td>{{ quiz.name }}</td></tr>
      <tr><td>Start at:</td><td>{{ quiz.start_at}}</td></tr>
      <tr><td>End at:</td><td>{{ quiz.end_at }}</td></tr>
    </table>
    <table border="1">
      <tr>
        <th>No.</th>
        <th>Question</th>
        <th>Options</th>
      </tr>
      {% for q in quiz.questions %}
      <tr>
        <td>{{ loop.index }}</td>
        <td>{{ q.text }}</td>
        <td><ul>
        {% for o in q.options %}
          <li>{% if o.is_correct %}✔️{% endif %} {{ o.text }}</li>
        {% endfor %}
        </ul></td>
      </tr>
      {% endfor %}
    </table>
  </body>
</html>

"""

MUTATION="""
mutation loadQuiz(
  $name: String!
  $start_at: timestamptz!
  $end_at: timestamptz!
  $questions: [qberry_questions_insert_input!]!
) {
  quiz: insert_qberry_quiz(objects:{
    name: $name
    start_at: $start_at
    end_at: $end_at
    questions: {
      data: $questions
    }
  }) {
    affected_rows
    returning {
      id
      name
      start_at
      end_at
      questions {
        text
        options {
          text
          is_correct
        }
      }
    }
  }
}
"""

def load_quiz(name, start_at, end_at, csv_file):
  stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
  questions = []
  csv_reader = csv.DictReader(stream)
  line_count = 0
  for row in csv_reader:
    line_count += 1
    question = {
      'text': row['question'],
      'options': {
        'data': [
          {
            'text': row['a'],
            'is_correct': 'a' == row['answer']
          },
          {
            'text': row['b'],
            'is_correct': 'b' == row['answer']
          },
          {
            'text': row['c'],
            'is_correct': 'c' == row['answer']
          },
          {
            'text': row['d'],
            'is_correct': 'd' == row['answer']
          }
        ]
      }
    }
    questions.append(question)

  variables = {
    'name': name,
    'start_at': start_at,
    'end_at': end_at,
    'questions': questions
  }
  
  payload = {
    'query': MUTATION,
    'variables': variables
  }
  
  r = requests.post(endpoint, json=payload, headers={'x-hasura-admin-secret':admin_secret})
  if r.status_code == 200:
    resp = r.json()
    if 'errors' in resp:
      raise Exception(resp.errors)
    return {
      'questions': line_count,
      'data': resp['data']
    }
  else:
    raise Exception(r.json())


@app.route('/', defaults={'path': ''}, methods=["GET", "POST"])
@app.route('/<path:path>', methods=["GET", "POST"])
def upload(path):
  if request.method == "GET":
    return Response(form_html, mimetype="text/html")

  if request.method == "POST":
    title = "Done"
    message = "Quiz saved"

    password = request.form.get('password')
    quiz_name = request.form.get('quiz_name')
    start_date = request.form.get('start_date')
    start_time = request.form.get('start_time')
    end_date = request.form.get('end_date')
    end_time = request.form.get('end_time')
    qs_file = request.files.get('qs_file')

    if password != admin_password:
      title = "Error!"
      message = "invalid password"
    else:
      try:
        resp = load_quiz(
          quiz_name,
          format_date_time(start_date, start_time),
          format_date_time(end_date, end_time),
          qs_file
        )
        quiz = resp['data']['quiz']['returning'][0]
        return Response(render_template_string(quiz_template, quiz=quiz), mimetype="text/html")
      except Exception as e:
        print(e)
        title = "Error!"
        message = e

    return Response("<h1>%s</h1><p>%s</p>" % (title, message), mimetype="text/html")

def format_date_time(d, t):
  return "%sT%s:00.000000+05:30" % (d, t)