using System.Collections.Generic;
using TMPro;
using UnityEngine;


// Stores references for everything needer to refer to in the scene.
public class SceneReferencer : TXRSingleton<SceneReferencer>
{
    //--------------Experiment Configurations--------------

    [Header("Experiment Configurations")]
    public int NumberOfQuestionsInSemiActiveTour = 3;

    [Header("Art Pieces")]
    public List<Piece> pieces;

    [Header("Demo Pieces")]
    public List<Piece> demoPieces;

    [Header("Demo Instructions")]
    public InstructionsBoard pressToStart;
    public InstructionsBoard welcomeToTheMuseum;
    public InstructionsBoard followTheArrowToTheFirstPiece;
    public InstructionsBoard pressTheButtonToHearAudio;
    public InstructionsBoard answerTheQuestion;
    public InstructionsBoard letsStartTheTour;
    public InstructionsBoard followTheArrow;

    [Header("Tour Instructions")]
    public InstructionsBoard endBoard;
    public InstructionsBoard endActiveOfChoice;

    [Header("Active Tour Questions")]
    public List<SerializedMultichoiceQuestion> questions;

    [Header("Demo Questions")]
    public List<SerializedMultichoiceQuestion> demoQuestions;

    //---------------------------FX--------------------------
    [Header("Buttons Glow Effect")]
    public bool shouldButtonGlow = false;
    public float globalGlowSpeed = 1.9f;
    public float globalMinGlow = 0.1f;               //also looks nice: min 0.05, max 0.8
    public float globalMaxGlow = 1.0f;

    //----------------------Game Objects----------------------
    [Space(20)]
    [Header("Game Objects")]
    public FloatingBoard floatingBoard;
    public MultiChoiceQuestion multiChoiceQuestion;
    public MultiChoiceQuestion typeQuestion;
    public GoToTarget DirectionArrow;
    public Collection artCollection;
    public Collection demoCollection;
    public TextMeshPro debugText;



}


