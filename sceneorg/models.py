import urllib
import urllib.request

from django.db import models


class Directory(models.Model):
    path = models.CharField(max_length=255, unique=True, db_index=True)
    is_deleted = models.BooleanField(default=False)
    first_seen_at = models.DateTimeField(null=True, auto_now_add=True)
    last_seen_at = models.DateTimeField()
    last_spidered_at = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey(
        "Directory", related_name="subdirectories", null=True, blank=True, on_delete=models.CASCADE
    )
    competitions = models.ManyToManyField("parties.Competition", related_name="sceneorg_directories")

    def mark_deleted(self):
        for dir in self.subdirectories.all():
            dir.mark_deleted()
        self.files.all().update(is_deleted=True)
        self.is_deleted = True
        self.save()

    def __str__(self):
        return self.path

    @property
    def web_url(self):
        return "https://files.scene.org/browse%s" % urllib.parse.quote(self.path.encode("utf-8"))

    def new_files_url(self, days):
        return "https://www.scene.org/newfiles.php?dayint=%s&dir=%s" % (
            days,
            urllib.parse.quote(self.path.encode("utf-8")),
        )

    @staticmethod
    def parties_root():
        return Directory.objects.get(path="/parties/")

    @staticmethod
    def party_years():
        return Directory.objects.filter(parent=Directory.parties_root())

    @staticmethod
    def parties():
        return Directory.objects.filter(parent__in=Directory.party_years())


class FileTooBig(Exception):
    pass


class File(models.Model):
    path = models.CharField(max_length=1023, unique=True, db_index=True)
    is_deleted = models.BooleanField(default=False)
    first_seen_at = models.DateTimeField(null=True, auto_now_add=True)
    last_seen_at = models.DateTimeField()
    directory = models.ForeignKey(Directory, related_name="files", on_delete=models.CASCADE)
    size = models.BigIntegerField(null=True)

    def __str__(self):
        return self.path

    def filename(self):
        return self.path.split("/")[-1]

    def fetched_data(self):
        # f = urllib.request.urlopen('http://http.de.scene.org/pub' + self.path)
        f = urllib.request.urlopen("ftp://ftp.scene.org/pub" + self.path)
        file_content = f.read(65537)
        f.close()
        if len(file_content) > 65536:
            raise FileTooBig("Cannot fetch files larger than 64Kb")
        return file_content

    @property
    def web_url(self):
        return "https://files.scene.org/browse%s" % urllib.parse.quote(self.path.encode("utf-8"))
