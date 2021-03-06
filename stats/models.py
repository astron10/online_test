# Django Imports
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Local Imports
from yaksh.models import Course, Lesson


def str_to_datetime(s):
    return timezone.datetime.strptime(s, '%H:%M:%S')


def str_to_time(s):
    return timezone.datetime.strptime(s, '%H:%M:%S').time()


def time_to_seconds(time):
    return timezone.timedelta(hours=time.hour, minutes=time.minute,
                              seconds=time.second).total_seconds()


class TrackLesson(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    current_time = models.CharField(max_length=100, default="00:00:00")
    video_duration = models.CharField(max_length=100, default="00:00:00")
    creation_time = models.DateTimeField(auto_now_add=True)
    watched = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'course', 'lesson')

    def get_log_counter(self):
        return self.lessonlog_set.count()

    def get_current_time(self):
        if self.current_time == '00:00:00':
            return 'just started'
        return self.current_time

    def get_video_duration(self):
        if self.video_duration == '00:00:00':
            return 'will be available after 25% completion'
        return self.video_duration

    def set_current_time(self, ct):
        t = timezone.datetime.strptime(ct, '%H:%M:%S').time()
        current = timezone.datetime.strptime(self.current_time,
                                             '%H:%M:%S').time()
        if t > current:
            self.current_time = ct

    def get_percentage_complete(self):
        if self.current_time == '00:00:00' and self.video_duration == '00:00:00':
            return 'less than 25%'
        duration = str_to_time(self.video_duration)
        watch_time = str_to_time(self.current_time)
        duration_seconds = time_to_seconds(duration)
        watched_seconds = time_to_seconds(watch_time)
        percentage = round((watched_seconds / duration_seconds) * 100)
        return 'approx {0} %'.format(percentage)


    def get_last_access_time(self):
        lesson_logs = self.lessonlog_set
        last_access_time = self.creation_time
        if lesson_logs.exists():
            last_access_time = lesson_logs.last().last_access_time
        return last_access_time

    def set_watched(self):
        if self.current_time != '00:00:00' and self.video_duration != '00:00:00':
            duration = str_to_time(self.video_duration)
            watch_time = (str_to_datetime(self.current_time) + timezone.timedelta(
                seconds=10)).time()
            self.watched = watch_time >= duration

    def get_watched(self):
        if not self.watched:
            self.set_watched()
            self.save()
        return self.watched


    def time_spent(self):
        if self.video_duration != '00:00:00':
            hits = self.get_log_counter()
            duration = str_to_time(self.video_duration)
            hit_duration = int((time_to_seconds(duration))/4)
            total_duration = hits * hit_duration
            return str(timezone.timedelta(seconds=total_duration))
        return self.get_current_time()

    def __str__(self):
        return (f"Track {self.lesson} in {self.course} "
                f"for {self.user.get_full_name()}")


class LessonLog(models.Model):
    track = models.ForeignKey(TrackLesson, on_delete=models.CASCADE)
    current_time = models.CharField(max_length=20, default="00:00:00")
    last_access_time = models.DateTimeField(default=timezone.now)
