from abc import ABC, abstractmethod
from pathlib import Path
from typing import NoReturn

import pygame
from pygame.math import Vector2

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
            self.clock.tick(144)
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
    def __init__(self, pos: Vector2) -> None:
        self.pos = pos
        self.color = (255, 0, 0)
        self.speed = 1.75

    def move(self, direction: Vector2) -> None:
        direction.scale_to_length(self.speed)
        self.pos += direction

    def render(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, self.color, self.pos, 10, 5)


class Obstacle:
    color = (255, 0, 255)

    def __init__(self, start_pos: Vector2, end_pos: Vector2) -> None:
        self.start_pos = start_pos
        self.end_pos = end_pos

    def render(self, screen: pygame.Surface) -> None:
        pygame.draw.line(screen, self.color, self.start_pos, self.end_pos, width=3)


class LightSource:
    color = (255, 255, 100)

    def __init__(self, pos: Vector2) -> None:
        self.pos = pos

    def line_of_sight_polygon(
        self,
        width: int,
        height: int,
        obstacles: list[Obstacle],
    ) -> list[Vector2]:
        rays = [
            (Vector2(0, 0) - self.pos).normalize(),
            (Vector2(width, 0) - self.pos).normalize(),
            (Vector2(0, height) - self.pos).normalize(),
            (Vector2(width, height) - self.pos).normalize(),
        ]
        for obs in obstacles:
            rays.append((obs.start_pos - self.pos).normalize())
            rays.append((obs.end_pos - self.pos).normalize())
        rays.sort(key=lambda v: v.as_polar()[1])
        poly = []
        for ray in rays:
            min_dist = 9001.0
            intersect_pre = None
            intersect_after = None
            for line in obstacles:
                t1t2 = intersect_ray_line(self.pos, ray, line.start_pos, line.end_pos)
                if t1t2 is not None:
                    t1, t2 = t1t2
                    if t2 == 0:
                        intersect_pre = t1
                    elif t2 == 1:
                        intersect_after = t1
                    elif t1 < min_dist:
                        min_dist = t1
            if intersect_pre is not None and intersect_pre < min_dist:
                poly.append(self.pos + ray * intersect_pre)
            poly.append(self.pos + ray * min_dist)
            if intersect_after is not None and intersect_after < min_dist:
                poly.append(self.pos + ray * intersect_after)
        return poly

    def render(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, self.color, self.pos, 5)


class GameScene(Scene):
    def __init__(self) -> None:
        self.player = Player(Vector2(20, 500))
        self.lights: list[LightSource] = [
            LightSource(Vector2(400, 100)),
            LightSource(Vector2(700, 150)),
        ]
        self.obstacles: list[Obstacle] = [
            Obstacle(Vector2(10, 550), Vector2(600, 550)),
            Obstacle(Vector2(300, 200), Vector2(400, 400)),
        ]

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((0, 0, 0))
        screen_width, screen_height = screen.get_size()

        self.player.render(screen)

        for light in self.lights:
            lighting = pygame.Surface((screen_width, screen_height))
            lighting.set_alpha(40)
            light.render(screen)
            poly = light.line_of_sight_polygon(
                screen_width, screen_height, self.obstacles
            )
            pygame.draw.polygon(lighting, (255, 255, 150), poly)
            screen.blit(lighting, (0, 0))

        for obstacle in self.obstacles:
            obstacle.render(screen)

    def update(self) -> None:
        keys = pygame.key.get_pressed()
        movement = Vector2()
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


def intersect_ray_line(
    origin: Vector2,
    direction: Vector2,
    p1: Vector2,
    p2: Vector2,
) -> tuple[float, float] | None:
    """
    Calculate distance from origin to a point where a ray going in a direction
    intersects a line segment defined by two points p1 and p2.
    Returns two numbers t1 and t2 where
    * t1 is the factor the "direction" ray needs to be multiplied by to get to
      the intersection
    * t2 is a number between 0 and 1 that describes where between p1 and p2 the
      intersection point was
    """
    epsilon = 0.00001
    v1 = origin - p1
    v2 = p2 - p1
    v3 = Vector2(-direction.y, direction.x)
    dot = v2 * v3
    if abs(dot) < epsilon:
        return None

    t1 = v2.cross(v1) / dot
    t2 = v1.dot(v3) / dot
    if t1 >= 0 and 0 <= t2 <= 1:
        return t1, t2

    return None


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
