from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone


class Journal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=350)
    date = models.DateField('Date')
    location = models.CharField(max_length=255, default='')

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('detail', kwargs={'pk': self.pk})  # Use 'pk' instead of 'journal_id'

class Entry(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='entry')
    title = models.CharField(max_length=50)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

class Comment(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)  # Add this line

    def __str__(self):
        return f"Comment by {self.user.username} on {self.journal.title}"

class Photo(models.Model):
    url = models.CharField(max_length=200)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)

    def __str__(self):
        return f"Photo for journal_id: {self.journal_id} @{self.url}"