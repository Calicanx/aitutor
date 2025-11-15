import React, { useEffect, useState, useRef } from "react";
import {ServerItemRenderer} from "../../package/perseus/src/server-item-renderer";
import type { PerseusItem } from "@khanacademy/perseus-core";
import { storybookDependenciesV2 } from "../../package/perseus/testing/test-dependencies";
import { scorePerseusItem } from "@khanacademy/perseus-score";
import { keScoreFromPerseusScore } from "../../package/perseus/src/util/scoring";
import { RenderStateRoot } from "@khanacademy/wonder-blocks-core";
import { PerseusI18nContextProvider } from "../../package/perseus/src/components/i18n-context";
import { mockStrings } from "../../package/perseus/src/strings";
import { KEScore } from "@khanacademy/perseus-core";

const RendererComponent = () => {
    const [perseusItems, setPerseusItems] = useState<PerseusItem[]>([]);
    const [item, setItem] = useState(0);
    const [loading, setLoading] = useState(true);
    const [endOfTest, setEndOfTest] = useState(false);
    const [score, setScore] = useState<KEScore>();
    const [isAnswered, setIsAnswered] = useState(false);
    const [startTime, setStartTime] = useState<number>(Date.now());
    const [age, setAge] = useState<number>(7); // Student age for cold-start (default: Grade 2)
    const rendererRef = useRef<ServerItemRenderer>(null);
    // Each age gets unique user ID for independent cold-start initialization
    const user_id = `student_age${age}`; // e.g., "student_age5", "student_age7", "student_age12"

    useEffect(() => {
        // Use DASH API with intelligent question selection
        // Include age parameter for cold-start initialization
        setLoading(true);
        setItem(0);
        setEndOfTest(false);
        setIsAnswered(false);
        
        fetch(`http://localhost:8000/api/questions/16?user_id=${user_id}&age=${age}`)
            .then((response) => response.json())
            .then((data) => {
                console.log("API response:", data);
                setPerseusItems(data);
                setLoading(false);
                setStartTime(Date.now()); // Reset timer for first question
            })
            .catch((err) => {
                console.error("Failed to fetch questions:", err);
                setLoading(false);
            });
    }, [age]); // Re-fetch when age changes

    // Log when question is displayed
    useEffect(() => {
        if (perseusItems.length > 0 && !loading) {
            const currentItem = perseusItems[item];
            const metadata = (currentItem as any).dash_metadata || {};
            
            fetch(`http://localhost:8000/api/question-displayed/${user_id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_index: item,
                    metadata: metadata
                })
            }).catch(err => console.error('Failed to log question display:', err));
        }
    }, [item, perseusItems, loading]);

    const handleNext = () => {
        setItem((prev) => {
            const index = prev + 1;

            if (index >= perseusItems.length) {
                setEndOfTest(true);
                return prev; // stay at last valid index
            }

            if (index === perseusItems.length - 1) {
                setEndOfTest(true);
            }

            setIsAnswered(false);
            setStartTime(Date.now()); // Reset timer for next question
            return index;
        });
    };


    const handleSubmit = async () => {
        if (rendererRef.current) {
            const userInput = rendererRef.current.getUserInput();
            const question = perseusItem.question;
            const score = scorePerseusItem(question, userInput, "en");

            // Continue to include an empty guess for the now defunct answer area.
            const maxCompatGuess = [rendererRef.current.getUserInputLegacy(), []];
            const keScore = keScoreFromPerseusScore(score, maxCompatGuess, rendererRef.current.getSerializedState().question);

            // Calculate response time
            const responseTimeSeconds = (Date.now() - startTime) / 1000;

            // Submit answer to DASH API for tracking and adaptive difficulty
            try {
                const currentItem = perseusItems[item];
                const metadata = (currentItem as any).dash_metadata || {};

                const answerData = {
                    question_id: metadata.dash_question_id || `q_${item}`,
                    skill_ids: metadata.skill_ids || ["counting_1_10"],
                    is_correct: keScore.correct,
                    response_time_seconds: responseTimeSeconds
                };

                const response = await fetch(`http://localhost:8000/api/submit-answer/${user_id}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(answerData),
                });

                const result = await response.json();
                console.log("Answer submitted to DASH:", result);
            } catch (error) {
                console.error("Failed to submit answer to DASH:", error);
            }

            // Display score to user
            setIsAnswered(true);
            setScore(keScore);
            console.log("Score:", keScore);
        }
    };

    const perseusItem = perseusItems[item] || {};

    return (
            <div className="framework-perseus">
                <div style={{ padding: "20px" }}>
                    {/* Age Selector for Testing Cold-Start */}
                    <div className="mb-6 p-4 bg-gray-100 rounded-lg border border-gray-300">
                        <div className="flex items-center gap-4">
                            <label className="font-semibold text-gray-700">
                                Student Age:
                            </label>
                            <select 
                                value={age} 
                                onChange={(e) => setAge(Number(e.target.value))}
                                className="border border-gray-400 p-2 rounded bg-white text-gray-800 cursor-pointer hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                disabled={loading}
                            >
                                <option value={5}>5 years (Kindergarten)</option>
                                <option value={6}>6 years (Grade 1)</option>
                                <option value={7}>7 years (Grade 2)</option>
                                <option value={8}>8 years (Grade 3)</option>
                                <option value={9}>9 years (Grade 4)</option>
                                <option value={10}>10 years (Grade 5)</option>
                                <option value={11}>11 years (Grade 6)</option>
                                <option value={12}>12 years (Grade 7)</option>
                                <option value={13}>13 years (Grade 8)</option>
                                <option value={14}>14 years (Grade 9)</option>
                                <option value={15}>15 years (Grade 10)</option>
                                <option value={16}>16 years (Grade 11)</option>
                                <option value={17}>17 years (Grade 12)</option>
                            </select>
                            <span className="text-sm text-gray-600 italic">
                                {loading ? "Loading questions..." : `${perseusItems.length} questions loaded`}
                            </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-2">
                            💡 Each age creates a separate student profile with grade-appropriate skills and questions.
                        </p>
                    </div>

                    <button
                        onClick={handleNext}
                        className="absolute top-19 right-8 bg-black rounded 
                            text-white p-2">Next</button>
                            
                    {endOfTest ? (
                        <p>You've successfully completed your test!</p>
                    ): (
                        perseusItems.length > 0 ? (
                        <div>
                            <PerseusI18nContextProvider locale="en" strings={mockStrings}>
                                <RenderStateRoot>
                                    <ServerItemRenderer
                                        ref={rendererRef}
                                        problemNum={0}
                                        item={perseusItem}
                                        dependencies={storybookDependenciesV2}
                                        apiOptions={{}}
                                        linterContext={{
                                            contentType: "",
                                            highlightLint: true,
                                            paths: [],
                                            stack: [],
                                        }}
                                        showSolutions="none"
                                        hintsVisible={0}
                                        reviewMode={false}
                                        />
                                </RenderStateRoot>
                            </PerseusI18nContextProvider>
                            {isAnswered && <div 
                                className="flex justify-between mt-9">
                                    <span className={score?.correct ? "text-green-400 italic" : "text-red-400 italic"}>
                                        {score?.correct ?(<p>Correct Answer!</p>):(<p>Wrong Answer.</p>)}
                                    </span>
                            </div>}
                        </div>
                        ) : (
                            <p>Loading...</p>
                        )
                    )}
                    <button 
                        className="bg-blue-500 absolute rounded text-white p-2 right-8 mt-8"
                        onClick={handleSubmit}>
                        Submit
                    </button>
                </div>
            </div>
    );
};

export default RendererComponent;
