import React, { useState } from "react";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Image from "react-bootstrap/Image";
import qberry from "../images/qberry.png"
import "../App.css";
import Button from "react-bootstrap/Button";
import ButtonGroup from "react-bootstrap/ButtonGroup";
import ButtonToolbar from "react-bootstrap/ButtonToolbar";
import Card from "react-bootstrap/Card";
import ListGroup from "react-bootstrap/ListGroup";
import { useParams } from 'react-router-dom';
import gql from 'graphql-tag';
import { useQuery, useMutation } from '@apollo/react-hooks';

const GET_QUESTIONS = gql`query getQuestionsForSession($quiz_id: uuid!) {
  questions: qberry_session_questions(where:{
    quiz_id: {_eq: $quiz_id}
  }) {
    question {
      id
      text
      options {
        id
        text
      }
    }
  }
}`;

const SUBMIT_ANSWERS = gql`mutation submitAnswer(
  $answers: [qberry_answers_insert_input!]!
) {
  answers: insert_qberry_answers(objects: $answers) {
    affected_rows
  }
}`;

const Quiz = () => {
  const { quizId } = useParams();
  const { data, loading, error } = useQuery(GET_QUESTIONS, { variables: { quiz_id: quizId } });
  const [answers, setAnswers] = useState({});
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);

  if (loading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>{error}</div>
  }

  if (!(data && data.questions && data.questions.length > 0)) {
    return <div>Unknown state: {data}</div>
  }

  const showNextQuestion = (e) => {
    setCurrentQuestionIdx(currentQuestionIdx + 1);
  }

  const showPreviousQuestion = (e) => {
    setCurrentQuestionIdx(currentQuestionIdx - 1);
  }

  const totalQuestions= data.questions.length;

  const submitAnswers = (e) => {

  }

  return (
    <Container fluid>
      <Row className="customCenter fullHeight">
        <Col sm={12} lg={5} className="d-none d-lg-block">
          <Image src={qberry} fluid />
        </Col>
        <Col csm={12} lg={7} className="customCenter contentContainer">
          <Card>
            <Card.Header as="h6">Question {currentQuestionIdx + 1}/{totalQuestions}</Card.Header>

            <Question question={data.questions[currentQuestionIdx].question} answers={answers} setAnswers={setAnswers} />

            <ButtonToolbar
              className="justify-content-between"
              aria-label="Toolbar with Button groups for next and previous"
              style={{ padding: '5px' }}
            >
              <Button disabled={currentQuestionIdx === 0} variant="outline-secondary" onClick={showPreviousQuestion}>&lt;</Button>
              {currentQuestionIdx === totalQuestions - 1 && (<Button variant="primary" onClick={submitAnswers}>Submit</Button>)}
              <Button disabled={currentQuestionIdx === totalQuestions - 1} variant="outline-secondary" onClick={showNextQuestion}>&gt;</Button>
            </ButtonToolbar>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

const Question = ({ question, answers, setAnswers }) => {
  const handleClick = (question_id, option_id) => {
    setAnswers({...answers, [question_id]: option_id});
  }
  return (
    <Card.Body>
      <Card.Title style={{ fontSize: '1.4em', padding: '20px' }}>{question.text}</Card.Title>
      <Card>
        <ListGroup variant="flush">
          {question.options.map((option) => (
            <ListGroup.Item
              style={{ cursor: 'pointer' }} 
              key={option.id}
              onClick={(e)=>{
                handleClick(question.id, option.id);
              }}
              active={answers[question.id] === option.id}
            >{option.text}</ListGroup.Item>
          ))}
        </ListGroup>
      </Card>
    </Card.Body>
  );
}

export default Quiz;
