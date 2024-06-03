import arcade
import arcade.gui
import os
from arcade.gui import UIInputText

pressed_start = False
entered_port = None
new_game = False
existing_game = False
entered_address = None
connect_port = None

class QuitButton(arcade.gui.UIFlatButton):
    def on_click(self, event: arcade.gui.UIOnClickEvent):
        arcade.exit()
        os._exit(0)

class MyWindow(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Start Window", resizable=True)
        
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        arcade.set_background_color(arcade.color.WHITE)

        self.v_box = arcade.gui.UIBoxLayout()

        text = "To start a new game just enter your port number in the first input text box and click the 'Start New Game' button. If you want to connect to an existing game enter the address and port number of a connected player and click the 'Connect to a game' button. If you want to quit the game click the 'Quit' button. The port number should be between 1024 and 65535. "
        ui_text_label = arcade.gui.UITextArea(text=text,
                                              width=450,
                                              height=130,
                                              font_size=13,
                                              font_name="Ubuntu-Regular.ttf",
                                              text_color=arcade.color.BLACK,)
        self.v_box.add(ui_text_label.with_space_around(bottom=3))
        # Add large text at the top
        instruction_label = arcade.gui.UILabel(
            text="Your port number:",
            font_size=15,
            text_color=arcade.color.BLACK,
            align="center",
            size_hint=(None, None)
        )
        self.v_box.add(instruction_label.with_space_around(bottom=10))

        # Create the input box with custom styling
        self.port_input_box = UIInputText(
            width=200,
            height=30,
            text="",
            placeholder="Enter your port",
            border_color=arcade.color.BLACK,
        ).with_border()
        
        self.v_box.add(self.port_input_box.with_space_around(bottom=10))

        # Add large text at the top
        instruction_label_2 = arcade.gui.UILabel(
            text="player address(1 for localhost, blank for none):",
            font_size=15,
            text_color=arcade.color.BLACK,
            align="center",
            size_hint=(None, None)
        )
        self.v_box.add(instruction_label_2.with_space_around(bottom=10))

         # Create the input box with custom styling
        self.address_input_box = UIInputText(
            width=200,
            height=30,
            text="",
            placeholder="Enter an address to connect to (blank for none/ 1 for localhost)",
            border_color=arcade.color.BLACK,
        ).with_border()
        self.v_box.add(self.address_input_box.with_space_around(bottom=20))


        # Add large text at the top
        instruction_label_3 = arcade.gui.UILabel(
            text="same player port number (blank for none):",
            font_size=15,
            text_color=arcade.color.BLACK,
            align="center",
            size_hint=(None, None)
        )
        self.v_box.add(instruction_label_3.with_space_around(bottom=10))

         # Create the input box with custom styling
        self.p_input_box = UIInputText(
            width=200,
            height=30,
            text="",
            placeholder="Enter an address to connect to (blank for none/ 1 for localhost)",
            border_color=arcade.color.BLACK,
        ).with_border()
        self.v_box.add(self.p_input_box.with_space_around(bottom=20))

        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
        )
        # Create the start button
        self.start_new_button = arcade.gui.UIFlatButton(text="Start New Game", width=200)
        self.start_new_button.on_click = self.on_click_start
        self.start_new_button.disabled = True  # Initially disabled
        self.v_box.add(self.start_new_button.with_space_around(bottom=20))

        self.connect_button = arcade.gui.UIFlatButton(text="Connect to a game", width=200)
        self.connect_button.on_click = self.on_click_connect
        self.connect_button.disabled = True  # Initially disabled
        self.v_box.add(self.connect_button.with_space_around(bottom=20))

        # Create the quit button
        quit_button = QuitButton(text="Quit", width=200)
        self.v_box.add(quit_button)

        self.port_input_box.on_change = self.on_port_change

    def on_port_change(self, event):
        try:
            port = int(self.port_input_box.text)
            if 1024 <= port <= 65535:  # Valid port range
                self.start_new_button.disabled = False
            else:
                self.start_new_button.disabled = True
        except ValueError:
            self.start_new_button.disabled = True

    def on_click_start(self, event):
        global pressed_start, entered_port, new_game
        new_game = True
        pressed_start = True
        entered_port = int(self.port_input_box.children[0].text)
        arcade.close_window()

    def on_click_connect(self, event):
        global pressed_start, entered_port, new_game, existing_game, entered_address, connect_port
        new_game = False
        existing_game = True
        pressed_start = True
        entered_port = int(self.port_input_box.children[0].text)
        entered_address = self.address_input_box.children[0].text
        connect_port = int(self.p_input_box.children[0].text)
        arcade.close_window()

    def on_draw(self):
        self.clear()
        self.manager.draw()

def run_start_window():
    window = MyWindow()
    arcade.run()