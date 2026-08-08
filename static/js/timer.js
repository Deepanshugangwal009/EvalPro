document.addEventListener('DOMContentLoaded', function () {
    var timerBox = document.getElementById('exam-timer');
    if (!timerBox) {
        return;
    }

    var examForm = document.getElementById('exam-form');
    var remainingSeconds = parseInt(timerBox.dataset.duration, 10) * 60;
    var timerId = null;

    function formatTime(totalSeconds) {
        var minutes = Math.floor(totalSeconds / 60);
        var seconds = totalSeconds % 60;
        return (minutes < 10 ? '0' : '') + minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
    }

    function showRemainingTime() {
        timerBox.textContent = formatTime(remainingSeconds);
        if (remainingSeconds <= 60) {
            timerBox.classList.add('text-danger');
        }
        if (remainingSeconds <= 0) {
            clearInterval(timerId);
            examForm.submit();
            return;
        }
        remainingSeconds -= 1;
    }

    showRemainingTime();
    timerId = setInterval(showRemainingTime, 1000);
});
