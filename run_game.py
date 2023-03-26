from abc import ABC, abstractmethod
from pathlib import Path
from typing import NoReturn

import pygame

ASSET_DIR = Path("./assets")


class Game:
    def __init__(self, window_size: tuple[int, int] = (800, 600)) -> None:
        self.window_size = window_size
        self.scenes = {
            "mainmenu": MainMenu(),
            "game": GameScene(),
        }
        self.scene = self.scenes["game"]
        self.clock = pygame.time.Clock()

    def run(self) -> NoReturn:
        pygame.display.set_caption("shadow game")
        pygame.font.init()
        screen = pygame.display.set_mode(self.window_size)
        while True:
            self.clock.tick(100)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    raise SystemExit(0)
                if event.type == pygame.USEREVENT:
                    if event.user_event == UserEvent.NEW_GAME:
                        self.scenes["game"] = GameScene()
                        self.scene = self.scenes["game"]
                    if event.user_event == UserEvent.SCENE_CHANGE:
                        screen.fill((0, 0, 0))
                        reset_cursor()
                        self.scene = self.scenes[event.scene]
            self.scene.handle_events(events)
            self.scene.update()
            self.scene.render(screen)
            pygame.display.flip()


class UserEvent:
    NEW_GAME = 1
    SCENE_CHANGE = 2

    @staticmethod
    def new_game() -> pygame.event.Event:
        return pygame.event.Event(
            pygame.USEREVENT,
            user_event=UserEvent.NEW_GAME,
        )

    @staticmethod
    def change_scene(scene_name: str) -> pygame.event.Event:
        return pygame.event.Event(
            pygame.USEREVENT,
            user_event=UserEvent.SCENE_CHANGE,
            scene=scene_name,
        )


class Scene(ABC):
    @abstractmethod
    def render(self, screen: pygame.Surface) -> None:
        ...

    @abstractmethod
    def update(self) -> None:
        ...

    @abstractmethod
    def handle_events(self, events: list[pygame.event.Event]) -> None:
        ...


class MainMenu(Scene):
    class Button:
        bg_focus_color = (15, 35, 25)
        bg_color = (10, 30, 20)
        text_color = (105, 255, 105)

        def __init__(self, text: str) -> None:
            font = pygame.font.SysFont("Arial", 40)
            antialiasing = True
            self.text_surface = font.render(text, antialiasing, self.text_color)
            self.text_width = self.text_surface.get_width()
            self.rect = pygame.Rect(0, 0, 0, 0)
            self.focus = False

        def clicked(self) -> None:
            pass

        def render(
                self,
                screen: pygame.Surface,
                rect: pygame.Rect,
        ) -> None:
            bg_color = self.bg_focus_color if self.focus else self.bg_color
            pygame.draw.rect(screen, bg_color, rect)
            text_left = rect.left + (rect.width - self.text_width) // 2
            screen.blit(self.text_surface, (text_left, rect.top))
            self.rect = rect

    class NewGameButton(Button):
        def clicked(self) -> None:
            pygame.event.post(UserEvent.new_game())

    class SettingsButton(Button):
        def clicked(self) -> None:
            print("settings")

    class QuitButton(Button):
        def clicked(self) -> None:
            raise SystemExit(0)

    def __init__(self) -> None:
        new_game = MainMenu.NewGameButton("New Game")
        settings = MainMenu.SettingsButton("Settings")
        quitbutton = MainMenu.QuitButton("Quit")
        self.buttons = [new_game, settings, quitbutton]
        self.logo = pygame.image.load(ASSET_DIR / "logo.png")

    def render(self, screen: pygame.Surface) -> None:
        screen_width = screen.get_width()

        # draw logo
        logo_left = (screen_width - self.logo.get_width()) // 2
        screen.blit(self.logo, (logo_left, 0))

        # draw buttons
        width = int(0.8 * screen_width)
        height = 50
        left = (screen_width - width) // 2
        top = 300
        rect = pygame.Rect(left, top, width, height)
        for button in self.buttons:
            button.render(screen, rect)
            rect = rect.move(0, height + 20)

    def update(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        cursor = pygame.SYSTEM_CURSOR_ARROW
        for button in self.buttons:
            button.focus = False
            if button.rect.collidepoint(mouse_pos):
                cursor = pygame.SYSTEM_CURSOR_HAND
                button.focus = True
        pygame.mouse.set_cursor(cursor)

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise SystemExit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    pygame.event.post(UserEvent.new_game())
                if event.key == pygame.K_c:
                    pygame.event.post(UserEvent.change_scene("game"))
            if event.type == pygame.MOUSEBUTTONUP:
                for button in self.buttons:
                    if button.rect.collidepoint(event.pos):
                        button.clicked()


class Player:
    def __init__(self) -> None:
        self.pos = pygame.math.Vector2()
        self.color = (255, 0, 0)
        self.speed = 3.0

    def move(self, direction: pygame.math.Vector2) -> None:
        direction.scale_to_length(self.speed)
        self.pos += direction

    def render(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, self.color, self.pos, 10, 5)


class GameScene(Scene):
    def __init__(self) -> None:
        self.player = Player()

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((0, 0, 0))
        self.player.render(screen)

    def update(self) -> None:
        keys = pygame.key.get_pressed()
        movement = pygame.math.Vector2()
        if keys[pygame.K_LEFT]:
            movement.x -= 1
        if keys[pygame.K_RIGHT]:
            movement.x += 1
        if keys[pygame.K_UP]:
            movement.y -= 1
        if keys[pygame.K_DOWN]:
            movement.y += 1
        if movement.length() > 0:
            self.player.move(movement)

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.event.post(UserEvent.change_scene("mainmenu"))


def reset_cursor() -> None:
    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)


def main() -> None:
    pygame.init()
    game = Game(window_size=(800, 600))
    try:
        game.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
