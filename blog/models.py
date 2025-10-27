from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)
    
    def __str__(self):
        return self.name
        
    

class Match(models.Model):
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    start_time = models.DateTimeField()
    
    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name}"


