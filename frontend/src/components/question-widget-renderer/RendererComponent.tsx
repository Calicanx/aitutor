import React, { useEffect, useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { ServerItemRenderer } from "../../package/perseus/src/server-item-renderer";
import type { PerseusItem } from "@khanacademy/perseus-core";
import { storybookDependenciesV2 } from "../../package/perseus/testing/test-dependencies";
import { scorePerseusItem } from "@khanacademy/perseus-score";
import { keScoreFromPerseusScore } from "../../package/perseus/src/util/scoring";
import { RenderStateRoot } from "@khanacademy/wonder-blocks-core";
import { PerseusI18nContextProvider } from "../../package/perseus/src/components/i18n-context";
import { mockStrings } from "../../package/perseus/src/strings";
import { KEScore } from "@khanacademy/perseus-core";
import { toast } from "sonner";
import { useDashQuestions } from "@/hooks/query-hooks/useDashQuestions";
import {
  useDashAnswerMutations,
  useTeachingAssistantQuestionAnswered,
} from "@/hooks/query-hooks/useDashAnswerMutations";

const TEACHING_ASSISTANT_API_URL = "http://localhost:8002";

const RendererComponent = () => {
    const [perseusItems, setPerseusItems] = useState<PerseusItem[]>([]);
    const [item, setItem] = useState(0);
    const [endOfTest, setEndOfTest] = useState(false);
    const [score, setScore] = useState<KEScore>();
    const [isAnswered, setIsAnswered] = useState(false);
    const [startTime, setStartTime] = useState<number>(Date.now());
    const rendererRef = useRef<ServerItemRenderer>(null);

    // User ID - age is now fetched from MongoDB, not frontend
    const user_id = "mongodb_test_user"; // Use the MongoDB test user

    const {
        data: questions,
        isLoading,
        isError,
        error,
    } = useDashQuestions({ userId: user_id, count: 16 });

    const { submitDashAnswer, logQuestionDisplayed } = useDashAnswerMutations();
    const teachingAssistantQuestionAnswered =
        useTeachingAssistantQuestionAnswered();

    useEffect(() => {
        if (isError) {
            const message =
                error instanceof Error ? error.message : "Unknown error fetching questions";
            toast.error("Unable to load questions", {
                description: message,
            });
        }
    }, [isError, error]);

    useEffect(() => {
        if (questions && questions.length > 0) {
            setPerseusItems(questions);
            setItem(0);
            setEndOfTest(false);
            setIsAnswered(false);
            setStartTime(Date.now());
        }
    }, [questions]);

    // Log when question is displayed (once per item change)
    useEffect(() => {
        if (perseusItems.length > 0 && !isLoading) {
            const currentItem = perseusItems[item];
            const metadata = (currentItem as any).dash_metadata || {};

            logQuestionDisplayed.mutate({
                userId: user_id,
                index: item,
                metadata,
            });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [item, perseusItems, isLoading, user_id]);

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
            const keScore = keScoreFromPerseusScore(
                score,
                maxCompatGuess,
                rendererRef.current.getSerializedState().question,
            );

            // Calculate response time
            const responseTimeSeconds = (Date.now() - startTime) / 1000;

            // Submit answer to DASH API for tracking and adaptive difficulty
            try {
                const currentItem = perseusItems[item];
                const metadata = (currentItem as any).dash_metadata || {};

                submitDashAnswer.mutate({
                    userId: user_id,
                    questionId: metadata.dash_question_id || `q_${item}`,
                    skillIds: metadata.skill_ids || ["counting_1_10"],
                    isCorrect: keScore.correct,
                    responseTimeSeconds,
                });
            } catch (error) {
                console.error("Failed to submit answer to DASH:", error);
            }

            // Display score to user
            setIsAnswered(true);
            setScore(keScore);
            console.log("Score:", keScore);

            // Record question answer with TeachingAssistant
            try {
                const currentItem = perseusItems[item];
                const metadata = (currentItem as any).dash_metadata || {};
                const questionId =
                    metadata.dash_question_id || `q_${item}_${Date.now()}`;
                teachingAssistantQuestionAnswered.mutate({
                    questionId,
                    isCorrect: keScore.correct || false,
                });
            } catch (error) {
                console.error("Error recording question answer:", error);
            }
        }
    };

    const perseusItem = perseusItems[item] || {};

    return (
        <div className="framework-perseus flex justify-center py-8">
            <Card className="flex w-full max-w-6xl h-[560px] md:h-[600px] flex-col shadow-lg border border-border/60 mb-28">
                <CardHeader className="space-y-2">
                    <div className="flex items-center max-w-fit justify-between gap-4">
                        <div className="space-y-1">
                            <CardTitle className="text-xl font-semibold">
                                Adaptive Practice Session
                            </CardTitle>
                            <CardDescription>
                                Age and grade are loaded from MongoDB based on the user profile.
                            </CardDescription>
                        </div>
                        <div className="text-right text-sm text-muted-foreground">
                            <div className="font-medium">User: {user_id}</div>
                            <div className="text-xs">
                                    {isLoading
                                    ? "Loading questions..."
                                    : `${perseusItems.length} questions loaded`}
                            </div>
                        </div>
                    </div>
                </CardHeader>

                <CardContent className="flex-1 space-y-4 overflow-hidden">
                    <div className="relative h-full w-full overflow-auto">
                        {endOfTest ? (
                            <div className="flex h-full items-center justify-center px-4 py-6 text-center">
                                <div className="max-w-md rounded-md border border-border/70 bg-muted/40 px-4 py-6">
                                    <p className="text-lg font-medium">
                                        🎉 You&apos;ve successfully completed your test!
                                    </p>
                                    <p className="mt-2 text-sm text-muted-foreground">
                                        You can review questions above or restart the session from
                                        the main controls.
                                    </p>
                                </div>
                            </div>
                        ) : isLoading ? (
                            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                                Loading questions...
                            </div>
                        ) : perseusItems.length > 0 ? (
                            <div className="space-y-4 px-2">
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

                                {isAnswered && (
                                    <div className="mt-4 flex items-center justify-between rounded-md border border-border/70 bg-muted/40 px-4 py-3">
                                        <span
                                            className={
                                                score?.correct
                                                    ? "text-sm font-medium text-emerald-500"
                                                    : "text-sm font-medium text-red-400"
                                            }
                                        >
                                            {score?.correct ? "Correct answer!" : "Wrong answer."}
                                        </span>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                                No questions available.
                            </div>
                        )}
                    </div>
                </CardContent>

                <CardFooter className="flex justify-end gap-3">
                    <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleNext}
                        disabled={isLoading || endOfTest || perseusItems.length === 0}
                    >
                        Next
                    </Button>
                    <Button
                        type="button"
                        size="sm"
                        onClick={handleSubmit}
                        disabled={isLoading || endOfTest || perseusItems.length === 0}
                    >
                        Submit
                    </Button>
                </CardFooter>
            </Card>
        </div>
    );
};

export default RendererComponent;
