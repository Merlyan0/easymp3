import sys

from PyQt5 import uic, QtCore
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMenu, QMessageBox

import os.path

import fleep


class Window(QMainWindow):
    """ Main window. """
    def __init__(self) -> None:
        super(Window, self).__init__()
        uic.loadUi('itog.ui', self)
        self.setWindowTitle('Easy MP3')

        """
        MAIN VARIABLES
        """
        # list with paths to music files
        self.files_list = list()

        # icons
        self.play_icon = QPixmap("img/play.png")
        self.pause_icon = QPixmap("img/pause.png")
        self.volume_icon = QPixmap("img/volume.png")
        self.mute_icon = QPixmap("img/mute.png")

        # other
        self.volume_dragging = False
        self.seeker_dragging = False

        self.currentIndex = 0
        self.selected = list()
        self.menu = ''

        """
        INITIALIZE
        """
        # player and playlist
        self.player = QMediaPlayer()
        self.playlist = QMediaPlaylist()

        # ui
        self.init_ui()

        # other
        self.songInit = True

        self.createFile()

        self.loadPlaylist()

    def init_ui(self) -> None:
        """ Initialize events and other. """
        """
        EVENTS
        """
        # media controls
        self.play_button.mousePressEvent = self.play_music
        self.mute_button.mousePressEvent = self.mute_music
        self.upload_button.mousePressEvent = self.upload_music
        self.next_button.mousePressEvent = self.next_song
        self.previous_button.mousePressEvent = self.previous_song

        # volume slider
        self.volume_slider.mousePressEvent = self.volumePressEvent
        self.volume_slider.mouseMoveEvent = self.volumeMoveEvent
        self.volume_slider.mouseReleaseEvent = self.volumeReleaseEvent

        # seeker
        self.seeker.mousePressEvent = self.seekerPressEvent
        self.seeker.mouseMoveEvent = self.seekerMoveEvent
        self.seeker.mouseReleaseEvent = self.seekerReleaseEvent

        self.playlist_list.customContextMenuRequested.connect(self.listContextMenu)

        """
        OTHER
        """
        self.playlist_list.clear()

        self.player.setPlaylist(self.playlist)
        self.player.positionChanged.connect(self.update_position)
        self.player.currentMediaChanged.connect(self.update_media)

    def loadPlaylist(self):
        a = open('playlists.txt').readlines()
        for i in a:
            if i != '' and i != '\n':
                self.playlist.addMedia(QMediaContent(QUrl(i.rstrip('\n'))))
        self.update_playlist_list()

    def createFile(self, info='') -> None:
        if not os.path.isfile("playlists.txt"):
            _ = open("playlists.txt", mode='w+')

    def play_music(self, _) -> None:
        """ Play or pause music. """
        if self.check_deleted_files():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Некоторые файлы не были найдены. Они удалены из плейлиста.")
            msg.setWindowTitle("Предупреждение")
            msg.exec_()

        if self.check_failed_files():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Некоторые файлы имеют недопустимый формат. Они удалены из плейлиста.")
            msg.setWindowTitle("Предупреждение")
            msg.exec_()

        self.createFile()
        with open("playlists.txt", 'w') as F:
            a = map(lambda x: x +'\n', self.files_list)
            F.writelines(a)

        if self.playlist.mediaCount() != 0:
            if self.player.state() == 1:
                self.player.pause()
                self.play_button.setPixmap(self.play_icon)
            else:
                self.player.play()
                self.play_button.setPixmap(self.pause_icon)

    def mute_music(self, _) -> None:
        """ Mute or unmute sound. """
        if self.player.isMuted():
            self.player.setMuted(False)
            self.mute_button.setPixmap(self.volume_icon)
            self.volume_slider.setStyleSheet("""
                        QProgressBar {
                            margin: 10px;
                            height: 5px;
                            border: 0px solid #555;
                            border-radius: 2px;
                            background-color: rgba(102, 102, 102, 255);
                        }
                        QProgressBar::chunk {
                            background-color: rgba(255, 255, 255, 255);
                            border-radius: 2px;
                            width: 1px;
                        }
                        """)
            self.volume_slider.setCursor(Qt.SizeHorCursor)
        else:
            self.player.setMuted(True)
            self.mute_button.setPixmap(self.mute_icon)
            self.volume_slider.setStyleSheet("""
                        QProgressBar {
                            margin: 10px;
                            height: 5px;
                            border: 0px solid #555;
                            border-radius: 2px;
                            background-color: rgba(102, 102, 102, 30);
                        }
                        QProgressBar::chunk {
                            background-color: rgba(255, 255, 255, 30);
                            border-radius: 2px;
                            width: 1px;
                        }
                        """)
            self.volume_slider.unsetCursor()

    """
    VOLUME SLIDER EVENTS
    """
    def volumePressEvent(self, event):
        """ Mouse clicked on volume slider. """
        self.volume_dragging = True
        value = (event.x() / self.volume_slider.width()) * self.volume_slider.maximum()
        self.player.setVolume(int(value))
        self.volume_slider.setValue(int(value))

    def volumeMoveEvent(self, event):
        """ Mouse clicked and moved on volume slider. """
        if self.volume_dragging:
            value = (event.x() / self.volume_slider.width()) * self.volume_slider.maximum()
            self.player.setVolume(int(value))
            self.volume_slider.setValue(int(value))

    def volumeReleaseEvent(self, _):
        """ If mouse clicked on volume slider. """
        self.volume_dragging = False

    """
    SEEKER EVENTS
    """
    def seekerPressEvent(self, event):
        """ Mouse clicked on seeker slider. """
        self.seeker_dragging = True
        value = (event.x() / self.seeker.width()) * self.seeker.maximum()
        self.player.setPosition(int((event.x() / self.seeker.width()) * self.player.duration()))
        self.seeker.setValue(int(value))

    def seekerMoveEvent(self, event):
        """ Mouse clicked and moved on seeker slider. """
        if self.seeker_dragging:
            value = (event.x() / self.seeker.width()) * self.seeker.maximum()
            self.player.setPosition(int((event.x() / self.seeker.width()) * self.player.duration()))
            self.seeker.setValue(int(value))

    def seekerReleaseEvent(self, _):
        """ If mouse clicked on seeker slider. """
        self.seeker_dragging = False

    def next_song(self, _) -> None:
        """ Change song to next. """
        if self.songInit:
            if self.playlist.currentIndex() == self.playlist.mediaCount() - 1:
                self.playlist.setCurrentIndex(0)
            else:
                self.playlist.setCurrentIndex(self.playlist.currentIndex() + 1)
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Дождитесь инициализации этой песни. Обычно это занимает несколько секунд.")
            msg.setWindowTitle("Предупреждение")
            msg.exec_()

    def previous_song(self, _) -> None:
        """ Change song to previous. """
        if self.seeker.value() > 2:
            self.player.setPosition(0)
        else:
            if self.playlist.currentIndex() != 0:
                self.playlist.setCurrentIndex(self.playlist.currentIndex() - 1)

    def upload_music(self, _) -> None:
        """ Open window to upload music files. """
        filename = QFileDialog.getOpenFileNames(self, 'Загрузить файлы')[0]
        if filename:
            for i in filename:
                self.playlist.addMedia(QMediaContent(QUrl(i)))
                self.files_list.append(i)
        self.update_playlist_list()

    def update_playlist_list(self) -> None:
        """ Update list with music files. """
        self.playlist_list.clear()
        self.files_list = list()
        for i in range(self.playlist.mediaCount()):
            self.playlist_list.addItem(f'{self.playlist.media(i).canonicalUrl().fileName().split(".")[0]}')
            self.files_list.append(f'{self.playlist.media(i).canonicalUrl().url()}')

    def check_deleted_files(self) -> bool:
        """ check files on deleted. """
        counter = -1
        find = False
        for i in self.files_list:
            counter += 1
            if not os.path.exists(i):
                self.playlist.removeMedia(counter)
                self.files_list.remove(i)
                find = True
        if find:
            self.update_playlist_list()
            return True
        return False

    def check_failed_files(self) -> bool:
        """ Check files for unknown format. """
        a = False
        b = list()
        for i in range(self.playlist.mediaCount()):
            with open(self.files_list[i], "rb") as file:
                info = fleep.get(file.read(128))
            if len(info.type) == 0:
                a = True
                b.append(i)
            elif info.type[0] != 'music' and info.type[0] != 'audio':
                a = True
                b.append(i)
        for i in reversed(b):
            self.playlist.removeMedia(i)
            del self.files_list[i]
        if a:
            self.update_playlist_list()
            return True
        return False

    def update_position(self, milliseconds: int):
        """ Update seeker position. """
        if self.player.duration():
            self.update_timestamp()
            self.seeker.setValue(int((milliseconds / self.player.duration()) * self.seeker.maximum()))
            duration = int(milliseconds / 1000)
            seconds = str(duration % 60)
            minutes = str(duration // 60)
            if int(seconds) <= 9:
                seconds = '0' + seconds
            if 1 <= int(minutes) < 10:
                minutes = '0' + minutes
            self.timestamp1.setText(str(minutes + ':' + seconds))

    def listContextMenu(self, pos):
        """ Open context menu in music playlist. """
        self.selected = self.playlist_list.selectedItems()
        if self.selected:
            self.menu = QMenu(self)
            self.menu.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            _ = self.menu.addAction("Удалить песню из плейлиста")
            self.menu.triggered.connect(self.itemClicked)
            self.menu.exec_(self.playlist_list.viewport().mapToGlobal(pos))
            self.menu.show()

    def itemClicked(self):
        """ If item clicked in list context menu. """
        for i in self.selected:
            self.playlist.removeMedia(self.playlist_list.row(i))
        self.update_playlist_list()
        self.menu.close()

    def update_timestamp(self):
        """ Update seeker timestamp. """
        duration = int(self.player.duration() / 1000)
        seconds = str(duration % 60)
        minutes = str(duration // 60)
        if int(seconds) <= 9:
            seconds = '0' + seconds
        if 1 <= int(minutes) < 10:
            minutes = '0' + minutes
        self.timestamp2.setText(minutes + ':' + seconds)

    def update_mediaInfo(self) -> None:
        """ Update song media info."""
        self.nowTitle.setText(str(self.playlist.currentMedia().canonicalUrl().fileName().split('.')[0]))

    def update_media(self):
        """ Update song media info."""
        """
        UPDATE TIMESTAMP
        """
        self.update_timestamp()

        """
        UPDATE NOW TITLE, ARTIST AND IMAGE
        """
        self.update_mediaInfo()
        """
        UPDATE NEXT TITLE AND ARTIST
        """
        if self.playlist.currentIndex() == self.playlist.mediaCount() - 1:
            next1 = 0
        else:
            next1 = self.playlist.currentIndex() + 1
        self.nextTitle.setText(str(self.playlist_list.item(next1).text()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
