using Cysharp.Threading.Tasks;
using System;
using System.Collections.Generic;
using UnityEngine;

public class SessionManager : TXRSingleton<SessionManager>
{
    [Tooltip("Editor Only!")]
    public bool skipDemo = false;

    //consts
    private const String ACTIVE_TYPE = "Type 1";
    private const String BOTH_TYPE = "Type 2";
    private const String PASSIVE_TYPE = "Type 3";
    private const int FIRST_PIECE_INDEX = 0;


    //config
    private String _experimentType;
    private int _maxQuestionsInSemiActiveTour;

    //game objects
    private FloatingBoard _floatingBoard;
    private MultiChoiceQuestion _multiChoiceQuestion;
    private MultiChoiceQuestion _expTypeQuestion;
    private List<Piece> _pieces;
    private List<Piece> _demoPieces;
    private List<SerializedMultichoiceQuestion> _questions;
    private List<SerializedMultichoiceQuestion> _demoQuestions;
    private GoToTarget _directionArrow;
    private List<List<String>> _activeTourQuestions = new List<List<String>>();
    private int question_index = 0;
    private Collection _artCollection;

    //Tour Instructions
    private InstructionsBoard _endBoard;
    private InstructionsBoard _endOfChoice;

    // demo objects
    private InstructionsBoard _pressToStart;
    private InstructionsBoard _welcomeToTheMuseum;
    private InstructionsBoard _followTheArrowTotheFirstPiece;
    private InstructionsBoard _pressTheButtonToHearAudio;
    private InstructionsBoard _answerTheQuestion;
    private InstructionsBoard _letsStartTheTour;
    private InstructionsBoard _followTheArrow;
    private Collection _demoCollection;

    //If there is a higher level flow manager, remove this and use his start method
    private void Start()
    {
        RunSessionFlow().Forget();
    }
    public async UniTask RunSessionFlow()
    {
        StartSession();

        await OperatorsInit();

        if (!UnityEngine.Application.isEditor || !skipDemo)
        {
            await PlayDemo();
        }

        await PlayTour();
        EndSession();
    }

    // setup session initial conditions.
    private void StartSession()
    {
        InitActiveTourQuestionsList();

        //get some references:
        _floatingBoard = SceneReferencer.Instance.floatingBoard;
        _pieces = SceneReferencer.Instance.pieces;
        _demoPieces = SceneReferencer.Instance.demoPieces;
        _multiChoiceQuestion = SceneReferencer.Instance.multiChoiceQuestion;
        _expTypeQuestion = SceneReferencer.Instance.typeQuestion;
        _maxQuestionsInSemiActiveTour = SceneReferencer.Instance.NumberOfQuestionsInSemiActiveTour;
        _questions = SceneReferencer.Instance.questions;
        _demoQuestions = SceneReferencer.Instance.demoQuestions;
        _directionArrow = SceneReferencer.Instance.DirectionArrow;
        _demoCollection = SceneReferencer.Instance.demoCollection;
        _artCollection = SceneReferencer.Instance.artCollection;
        _endBoard = SceneReferencer.Instance.endBoard;
        _endOfChoice = SceneReferencer.Instance.endActiveOfChoice;

        //make sure everything is hidden
        foreach (Piece p in _pieces)
        {
            //p.arrow.gameObject.SetActive(false);
            p.audioGuideButton.gameObject.SetActive(false);
        }

        foreach (Piece p in _demoPieces)
        {
            //p.arrow.gameObject.SetActive(false);
            p.audioGuideButton.gameObject.SetActive(false);
        }
        _multiChoiceQuestion.gameObject.SetActive(false);
        _expTypeQuestion.gameObject.SetActive(false);
        _directionArrow.Hide();
        _demoCollection.SetVisibilityImmediate(0f);
        _artCollection.SetVisibilityImmediate(0f);



        _welcomeToTheMuseum = SceneReferencer.Instance.welcomeToTheMuseum;
        _followTheArrowTotheFirstPiece = SceneReferencer.Instance.followTheArrowToTheFirstPiece;
        _pressTheButtonToHearAudio = SceneReferencer.Instance.pressTheButtonToHearAudio;
        _answerTheQuestion = SceneReferencer.Instance.answerTheQuestion;
        _letsStartTheTour = SceneReferencer.Instance.letsStartTheTour;
        _followTheArrow = SceneReferencer.Instance.followTheArrow;
        _pressToStart = SceneReferencer.Instance.pressToStart;
    }
    private void InitActiveTourQuestionsList()
    {
        List<SerializedMultichoiceQuestion> MultichoiceQuestions = SceneReferencer.Instance.questions;
        foreach (SerializedMultichoiceQuestion q in MultichoiceQuestions)
        {
            _activeTourQuestions.Add(new List<String> { q.Question, q.Answer1, q.Answer2, q.Answer3 });
        }

    }

    // experiment operator chooses type of experiment, etc
    private async UniTask OperatorsInit()
    {
        //wait for calibration to finish
        await _floatingBoard.ShowTextUntilContinue("Press continue when you've finished calibrating");
        await UniTask.Delay(TimeSpan.FromSeconds(1));

        //set experiment type
        MultichoiceAnswer.OnAnswerSelected.AddListener(processExperimentType);
        await _expTypeQuestion.SetAnswersAndAndWaitForAnswer(ACTIVE_TYPE, BOTH_TYPE, PASSIVE_TYPE);
        MultichoiceAnswer.OnAnswerSelected.RemoveListener(processExperimentType);
        await UniTask.Delay(TimeSpan.FromSeconds(1));

        //validate with operator
        await _floatingBoard.ShowTextUntilContinue("Starting " + _experimentType + " tour");
        await UniTask.Delay(TimeSpan.FromSeconds(1));
    }

    private void processExperimentType(string selectedAnswer)
    {
        _experimentType = selectedAnswer;

        string message = "Selected experiment type: " + _experimentType + ", ";
        switch (_experimentType)
        {
            case ACTIVE_TYPE:
                message += "Active";
                break;
            case PASSIVE_TYPE:
                message += "Passive";
                break;
            case BOTH_TYPE:
                message += "Semi-active/both";
                break;
            default:
                message = "something went wrong with tour type selection";
                break;
        }


        print(message);
        TXRDataManager.Instance.LogLineToFile(message);
    }

    private void SetQuestionPosition(Transform Positioner)
    {
        _multiChoiceQuestion.transform.position = Positioner.position;
        _multiChoiceQuestion.transform.rotation = Positioner.rotation;
    }

    private void SetBoardPosition(InstructionsBoard board, Transform Positioner)
    {
        board.transform.position = Positioner.position;
        board.transform.rotation = Positioner.rotation;
        board.transform.Rotate(0, 180, 0); //fix rotation so that the board is facing forward
    }

    private async UniTask ShowNextQuestion()
    {
        await _multiChoiceQuestion.SetAnswersAndAndWaitForAnswer(_questions[question_index].Answer1, _questions[question_index].Answer2, _questions[question_index].Answer3);
        await UniTask.Delay(TimeSpan.FromSeconds(1));
        question_index++;
    }

    private async UniTask PlayDemo()
    {
        await _pressToStart.ShowUntilContinuePressed();

        Debug.Log("Playing demo");

        //Instructions, direction arrow:
        await _welcomeToTheMuseum.ShowUntilContinuePressed();
        _directionArrow.ShowAndSetTarget(_demoPieces[FIRST_PIECE_INDEX].imageComponent.transform, false).Forget();
        await _followTheArrowTotheFirstPiece.ShowUntilAudioEnds();

        _demoCollection.FadeIn();

        //First piece:
        //_demoPieces[FIRST_PIECE_INDEX].arrow.gameObject.SetActive(true);
        _demoPieces[FIRST_PIECE_INDEX].audioGuideButton.gameObject.SetActive(true);
        _demoPieces[FIRST_PIECE_INDEX].proximityDetector.Activate();
        _pressTheButtonToHearAudio.Show(false);

        await _demoPieces[FIRST_PIECE_INDEX].audioGuideButton.waitForPress();

        _pressTheButtonToHearAudio.HideAndWaitForAnimation().Forget();

        await _demoPieces[FIRST_PIECE_INDEX].audioGuideButton.WaitForAudioGuideToFinish();

        _demoPieces[FIRST_PIECE_INDEX].audioGuideButton.gameObject.SetActive(false);

        // Active mode question:
        if (_experimentType == ACTIVE_TYPE || _experimentType == BOTH_TYPE)
        {

            SetQuestionPosition(_demoPieces[FIRST_PIECE_INDEX].questionBoardPositioner);

            await _answerTheQuestion.ShowUntilAudioEnds();

            await _multiChoiceQuestion.SetAnswersAndAndWaitForAnswer(_demoQuestions[0].Answer1, _demoQuestions[0].Answer2, _demoQuestions[0].Answer3);
            await UniTask.Delay(TimeSpan.FromSeconds(1));

        }
        _demoPieces[FIRST_PIECE_INDEX].proximityDetector.Deactivate();

        //Second piece:
        //_demoPieces[1].arrow.gameObject.SetActive(true);
        _demoPieces[1].audioGuideButton.gameObject.SetActive(true);
        _demoPieces[1].proximityDetector.Activate();
        _directionArrow.ShowAndSetTarget(_demoPieces[1].imageComponent.transform, true).Forget();
        _followTheArrow.ShowUntilAudioEnds().Forget();
        await _demoPieces[1].audioGuideButton.waitForPress();
        _demoPieces[1].audioGuideButton.WaitForAudioGuideToFinish().Forget();
        _demoPieces[1].audioGuideButton.gameObject.SetActive(false);
        _demoPieces[1].proximityDetector.Deactivate();

        await _letsStartTheTour.ShowUntilContinuePressed();
        _demoCollection.FadeOut();

    }

    private async UniTask PlayTour()
    {
        Debug.Log("Playing Tour");
        _artCollection.FadeIn();

        ArtPieceColliderExporter.ExportCollidersAsync(_pieces).Forget(); // shpold be after fade in so that the image colliders are turned on, enabling position recording

        int lastQuestionInSemiTourIndex = _maxQuestionsInSemiActiveTour - 1;
        int endPieceIndex = _pieces.Count - 1;

        foreach (Piece p in _pieces)
        {
            int pieceIndex = _pieces.IndexOf(p);
            //p.arrow.gameObject.SetActive(true);
            p.audioGuideButton.gameObject.SetActive(true);
            p.proximityDetector.Activate();
            _directionArrow.ShowAndSetTarget(p.imageComponent.transform, true).Forget();
            await p.audioGuideButton.WaitForAudioGuideToFinish();

            p.audioGuideButton.gameObject.SetActive(false);

            //should we show the question?
            switch (_experimentType)
            {
                case PASSIVE_TYPE:
                    break;

                // If the experiment type is active or both (but than the piece index is within the active range), show the question
                case ACTIVE_TYPE:
                    if (pieceIndex <= endPieceIndex - 1)
                    {
                        SetQuestionPosition(p.questionBoardPositioner);
                        await ShowNextQuestion();
                    }
                    break;
                case BOTH_TYPE:
                    if (pieceIndex <= lastQuestionInSemiTourIndex)
                    {

                        SetQuestionPosition(p.questionBoardPositioner);
                        await ShowNextQuestion();

                    }
                    else if (pieceIndex == lastQuestionInSemiTourIndex + 1)
                    {
                        SetBoardPosition(_endOfChoice, p.questionBoardPositioner);
                        await _endOfChoice.ShowUntilContinuePressed();
                    }
                    break;
            }
            p.proximityDetector.Deactivate();
        }

        SetBoardPosition(_endBoard, _pieces[endPieceIndex].questionBoardPositioner);
        await _endBoard.ShowUntilContinuePressed();
    }
    private void EndSession()
    {
        // setup end session conditions
        Application.Quit();
    }

    #region Obsolete
    //general method to display a list of instructions on the floating board one after the other
    private async UniTask ShowInstructions(List<TextAndScaleTuple> instructions)
    {
        foreach (TextAndScaleTuple instruction in instructions)
        {
            //check if the instruction should be shown
            bool shouldShowMsg;


            //if none is checked, show the message
            if (!(instruction.active || instruction.passive || instruction.semi))
            {
                shouldShowMsg = true;
            }
            else
            {
                switch (_experimentType)
                {
                    case ACTIVE_TYPE:
                        shouldShowMsg = instruction.active;
                        break;
                    case PASSIVE_TYPE:
                        shouldShowMsg = instruction.passive;
                        break;
                    case BOTH_TYPE:
                        shouldShowMsg = instruction.semi;
                        break;
                    default:
                        shouldShowMsg = false;
                        break;
                }
            }

            //print("should show msg (mumber " + instructions.IndexOf(instruction) + "): " + shouldShowMsg);

            //show the instruction
            if (shouldShowMsg)
            {
                await _floatingBoard.ShowTextAndScaleUntilContinue(instruction);
                await UniTask.Delay(TimeSpan.FromSeconds(1));
            }
        }
    }
    #endregion
}
