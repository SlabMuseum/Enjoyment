using Cysharp.Threading.Tasks;

public interface Question
{
    public UniTask WaitForAnswer();
}
