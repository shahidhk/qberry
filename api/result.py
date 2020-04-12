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
    <title>Qberry Admin | Results</title>
  </head>
  <body>
    <h1>Qberry Admin | Results</h1>
    <form method="POST">
      <table>
      <tr>
        <td><label for="password">Password:</label></td>
        <td><input type="password" id="password" name="password" required></td>
      </tr>

      <tr>
        <td><label for="quiz_id">Quiz ID:</label></td>
        <td><input type="text" id="quiz_id" name="quiz_id" required></td>
      </tr>

      <tr>
        <td><label for="num_winners">No. of winners:</label></td>
        <td><input type="number" id="num_winners" name="num_winners" required></td>
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

result_template = """
<html>
  <head>
    <title>Qberry Admin | Results</title>
  </head>
  <body>
    <h1>Qberry Admin | Results</h1>
    <table border="1">
      <tr>
      {% for c in header %}
        <th>{{ c }}</th>
      {% endfor %}
      </tr>
      {% for w in winners %}
      <tr>
        {% for c in w %}
          <td>{{ c }}</td>
        {% endfor %}
      </tr>
      {% endfor %}
    </table>
  </body>
</html>
"""

RESULT_SQL="""
SELECT
        name
       ,class
       ,school
       ,address
       ,mobile
       ,email
    FROM
        qberry.scores JOIN qberry.users
            ON qberry.scores.user_id = qberry.users.id
    WHERE
        qberry.scores.score = {{ max_score }}
        AND qberry.scores.quiz_id = '{{ quiz_id }}'
    ORDER BY
        random ()
    LIMIT {{ num_winners }}
"""

def get_result(quiz_id, max_score, num_winners):

  sql = render_template_string(RESULT_SQL, quiz_id=quiz_id, max_score=max_score, num_winners=num_winners)
  
  payload = {
    'type': 'run_sql',
    'args': {
      'sql': sql
    }
  }
  
  r = requests.post(endpoint.replace('graphql', 'query'), json=payload, headers={'x-hasura-admin-secret':admin_secret})
  if r.status_code == 200:
    resp = r.json()
    if 'errors' in resp:
      raise Exception(resp.errors)
    print(resp)
    return resp
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

    quiz_id = request.form.get('quiz_id')
    num_winners = request.form.get('num_winners')
    password = request.form.get('password')

    if password != admin_password:
      title = "Error!"
      message = "invalid password"
    else:
      try:
        resp = get_result(
          quiz_id,
          '5',
          num_winners
        )
        result = resp['result']
        header = result[0]
        winners = result[1:]
        return Response(render_template_string(result_template, header=header, winners=winners), mimetype="text/html")
      except Exception as e:
        print(e)
        title = "Error!"
        message = e

    return Response("<h1>%s</h1><p>%s</p>" % (title, message), mimetype="text/html")

def format_date_time(d, t):
  return "%sT%s:00.000000+05:30" % (d, t)