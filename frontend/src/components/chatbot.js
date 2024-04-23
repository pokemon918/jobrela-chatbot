import React, { useState } from "react";
import { Input, Button } from "rsuite";
import ReactMarkdown from "react-markdown";
import axios from "axios";
import _ from "lodash";
import apiUrl from "./../utils/api";

export function Chatbot() {
  const [isFinishedConversation, setFinishedConversation] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState([]);
  const sendQuestion = async () => {
    setFinishedConversation(true);
    const params = {
      query: chatInput,
    };
    try {
      const response = await axios.get(`${apiUrl}/professional`, {
        params,
      });
      const temp = questions;
      const tmp = answers;
      temp.push(chatInput);
      tmp.push(response.data);
      setQuestions(temp);
      setAnswers(tmp);
    } catch (err) {
      console.log(err);
    } finally {
      setFinishedConversation(false);
    }
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    sendQuestion();
    setChatInput("");
  };
  return (
    <div style={{ width: "100%", marginTop: 32, height: "100%" }}>
      <div
        style={{
          border: "1px solid gray",
          borderRadius: 12,
          background: "white",
          height: "calc(100% - 90px)",
          marginBottom: 20,
          overflowY: "auto",
        }}
      >
        {_.map(answers, (ans, id) => {
          return (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                padding: "4px 6px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyItems: "start",
                  color: "#1a0400",
                  margin: 4,
                }}
              >
                <div
                  style={{
                    background: "#fae5ca",
                    padding: 12,
                    borderRadius: 12,
                  }}
                >
                  <p style={{ fontSize: 16 }}>{questions[id]}</p>
                </div>
              </div>
              <div
                style={{
                  display: "flex",
                  justifyItems: "start",
                  color: "white",
                  margin: 4,
                }}
              >
                <div
                  style={{
                    background: "#579FFB",
                    padding: 12,
                    borderRadius: 12,
                    fontSize: 16,
                  }}
                >
                  <ReactMarkdown>{answers[id]}</ReactMarkdown>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div>
        <form onSubmit={handleSubmit} style={{ display: "flex", gap: 24 }}>
          <Input
            type="text"
            placeholder="Write down your question."
            size="lg"
            value={chatInput}
            disabled={isFinishedConversation}
            onChange={(value) => setChatInput(value)}
          />
          <Button
            type="submit"
            appearance="primary"
            style={{ padding: "0px 24px" }}
            disabled={isFinishedConversation || chatInput === ""}
          >
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}

export default Chatbot;
