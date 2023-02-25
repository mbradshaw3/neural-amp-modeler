# File: gui.py
# Created Date: Tuesday December 20th 2022
# Author: Steven Atkinson (steven@atkinson.mn)

"""
GUI for training
"""

import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from functools import partial
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional, Sequence

try:
    from nam.models.base import Model
    from nam.train import gui as _gui

    _install_is_valid = True
except ImportError:
    _install_is_valid = False

BUTTON_WIDTH = 20
BUTTON_HEIGHT = 2
TEXT_WIDTH = 70


@dataclass
class _AdvancedOptions(object):
    architecture: _gui.Architecture
    num_epochs: int
    delay: Optional[int]


class _PathType(Enum):
    FILE = "file"
    DIRECTORY = "directory"


class _PathButton(object):
    """
    Button and the path
    """

    def __init__(
        self,
        frame: tk.Frame,
        button_text,
        info_str: str,
        path_type: _PathType,
        hooks: Optional[Sequence[Callable[[], None]]] = None,
    ):
        self._info_str = info_str
        self._path: Optional[Path] = None
        self._path_type = path_type
        self._button = tk.Button(
            frame,
            text=button_text,
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            fg="black",
            command=self._set_val,
        )
        self._button.pack(side=tk.LEFT)
        self._label = tk.Label(
            frame,
            width=TEXT_WIDTH,
            height=BUTTON_HEIGHT,
            fg="black",
            bg=None,
            anchor="w",
        )
        self._label.pack(side=tk.RIGHT)
        self._hooks = hooks
        self._set_text()

    @property
    def val(self) -> Optional[Path]:
        return self._path

    def _set_text(self):
        if self._path is None:
            self._label["fg"] = "red"
            self._label["text"] = f"{self._info_str} is not set!"
        else:
            self._label["fg"] = "black"
            self._label["text"] = f"{self._info_str} set to {self.val}"

    def _set_val(self):
        res = {
            _PathType.FILE: filedialog.askopenfilename,
            _PathType.DIRECTORY: filedialog.askdirectory,
        }[self._path_type]()
        if res != "":
            self._path = res
        self._set_text()

        if self._hooks is not None:
            for h in self._hooks:
                h()


class GUI(object):
    def __init__(self):
        self._root = tk.Tk("NAM Trainer")

        # Buttons for paths:
        self._frame_input_path = tk.Frame(self._root)
        self._frame_input_path.pack()
        self._path_button_input = _PathButton(
            self._frame_input_path,
            "Input Audio",
            "Input audio",
            _PathType.FILE,
            hooks=[self._check_button_states],
        )

        self._frame_output_path = tk.Frame(self._root)
        self._frame_output_path.pack()
        self._path_button_output = _PathButton(
            self._frame_output_path,
            "Output Audio",
            "Output audio",
            _PathType.FILE,
            hooks=[self._check_button_states],
        )

        self._frame_train_destination = tk.Frame(self._root)
        self._frame_train_destination.pack()
        self._path_button_train_destination = _PathButton(
            self._frame_train_destination,
            "Train Destination",
            "Train destination",
            _PathType.DIRECTORY,
            hooks=[self._check_button_states],
        )

        # Advanced options for training
        default_architecture = _gui.Architecture.STANDARD
        default_num_epochs = 100
        default_delay = None
        self.advanced_options = _AdvancedOptions(
            default_architecture, default_num_epochs, default_delay
        )
        self._frame_advanced_options = tk.Frame(self._root)
        self._frame_advanced_options.pack()
        self._button_advanced_options = tk.Button(
            self._frame_advanced_options,
            text="Advanced options...",
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            fg="black",
            command=self._open_advanced_options,
        )
        self._button_advanced_options.pack()

        # Train button
        self._frame_train = tk.Frame(self._root)
        self._frame_train.pack()
        self._button_train = tk.Button(
            self._frame_train,
            text="Train",
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            fg="black",
            command=self._train,
        )
        self._button_train.pack()

        self._check_button_states()

    def mainloop(self):
        self._root.mainloop()

    def _open_advanced_options(self):
        """
        Open advanced options
        """
        ao = _AdvancedOptionsGUI(self)
        # I should probably disable the main GUI...
        ao.mainloop()
        # ...and then re-enable it once it gets closed.

    def _train(self):
        # Advanced options:
        num_epochs = self.advanced_options.num_epochs
        architecture = self.advanced_options.architecture
        delay = self.advanced_options.delay

        # Advanced-er options
        # If you're poking around looking for these, then maybe it's time to learn to
        # use the command-line scripts ;)
        lr = 0.004
        lr_decay = 0.007
        seed = 0

        # Run it
        trained_model = _gui.train(
            self._path_button_input.val,
            self._path_button_output.val,
            self._path_button_train_destination.val,
            epochs=num_epochs,
            delay=delay,
            architecture=architecture,
            lr=lr,
            lr_decay=lr_decay,
            seed=seed,
        )
        print("Model training complete!")
        print("Exporting...")
        outdir = self._path_button_train_destination.val
        print(f"Exporting trained model to {outdir}...")
        trained_model.net.export(outdir)
        print("Done!")

    def _check_button_states(self):
        """
        Determine if any buttons should be disabled
        """
        # Train button is diabled unless all paths are set
        if any(
            pb.val is None
            for pb in (
                self._path_button_input,
                self._path_button_output,
                self._path_button_train_destination,
            )
        ):
            self._button_train["state"] = tk.DISABLED
            return
        self._button_train["state"] = tk.NORMAL


_ADVANCED_OPTIONS_LEFT_WIDTH = 12
_ADVANCED_OPTIONS_RIGHT_WIDTH = 12


class _LabeledRadio(object):
    """
    Label (left) and radio buttons (right)
    """

    def __init__(
        self, frame: tk.Frame, label: str, choices: Enum, command: Callable[[Enum], None]
    ):
        """
        :param command: Called to propagate option selection. Is provided with the
            value corresponding to the radio button selected.
        """
        self._frame = frame
        height_per_option = 1  # BUTTON_HEIGHT
        height = height_per_option * len(choices)
        self._label = tk.Label(
            frame,
            width=_ADVANCED_OPTIONS_LEFT_WIDTH,
            height=height,
            fg="black",
            bg=None,
            anchor="w",
            text=label,
        )
        self._label.pack(side=tk.LEFT)

        frame_radios = tk.Frame(frame)
        frame_radios.pack(side=tk.RIGHT)

        # One Radiobutton per option?
        self._radios = {}
        for i, choice in enumerate(choices):
            self._radios[choice] = tk.Radiobutton(
                frame_radios,
                width=_ADVANCED_OPTIONS_RIGHT_WIDTH,
                height=height_per_option,
                text=choice.value,
                command=partial(self._command, choice),
                # justify=tk.LEFT,
                anchor="w",
                # state=tk.ACTIVE if i == 0 else tk.DISABLED
            )
            self._radios[choice].pack()
            if i > 0:
                self._radios[choice].deselect()

        # All in a single Radiobutton?
        # self._radio = tk.Radiobutton(
        #     frame_radios,
        #     width=60,  # _ADVANCED_OPTIONS_RIGHT_WIDTH,
        #     height=height,  #height_per_option,
        #     # text={choice.value: choice.value for choice in choices},
        #     textvariable=[choice.value for choice in choices],
        #     command=command,
        #     anchor="w"
        # )
        # self._radio.pack()

        print("Radios initialized")
        self._hook = command

    def get(self):
        # FIXME
        choice = list(self._radios.keys())[0]
        return choice

    def _command(self, selected):
        for key, val in self._radios.items():
            if key == selected:
                val["state"] = tk.NORMAL
            else:
                val["state"] = tk.DISABLED
        self._hook(selected)
        

class _LabeledText(object):
    """
    Label (left) and text input (right)
    """

    def __init__(
        self, frame: tk.Frame, label: str, default=None, type=None
    ):
        """
        :param command: Called to propagate option selection. Is provided with the
            value corresponding to the radio button selected.
        :param type: If provided, casts value to given type
        """
        self._frame = frame
        label_height = 2
        text_height = 1
        self._label = tk.Label(
            frame,
            width=_ADVANCED_OPTIONS_LEFT_WIDTH,
            height=label_height,
            fg="black",
            bg=None,
            anchor="w",
            text=label,
        )
        self._label.pack(side=tk.LEFT)

        self._text = tk.Text(
            frame,
            width=_ADVANCED_OPTIONS_RIGHT_WIDTH,
            height=text_height,
            fg="black",
            bg=None
        )
        self._text.pack(side=tk.RIGHT)
        # if default is not None:
        #     self._text.insert(0, str(default))

        print("Text initialized")

    def get(self):
        try:
            val = self._text.get(0)
            if self._type is not None:
                val = self._type(val)
            return val
        except tk.TclError:
            return None


class _AdvancedOptionsGUI(object):
    """
    A window to hold advanced options (Architecture and number of epochs)
    """

    def __init__(self, parent: GUI):
        self._parent = parent
        self._root = tk.Tk()

        # Architecture: radio buttons
        self._frame_architecture = tk.Frame(self._root)
        self._frame_architecture.pack()
        self._architecture = _LabeledRadio(
            self._frame_architecture,
            "Architecture",
            _gui.Architecture,
            self._set_architecture,
        )

        # Number of epochs: text box
        self._frame_epochs = tk.Frame(self._root)
        self._frame_epochs.pack()
        def non_negative_int(val):
            val = int(val)
            if val < 0:
                val = 0
            return val

        self._epochs = _LabeledText(self._frame_epochs, "Epochs", default=self._parent.advanced_options.num_epochs, type=non_negative_int)

        # Delay: text box
        self._frame_delay = tk.Frame(self._root)
        self._frame_delay.pack()
        self._delay = _LabeledText(self._frame_delay, "Delay", default=self._parent.advanced_options.delay, type=int)

        # "Ok": apply and destory
        self._frame_ok = tk.Frame(self._root)
        self._frame_ok.pack()
        self._button_ok = tk.Button(
            self._frame_ok,
            text="Ok",
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            fg="black",
            command=self._apply_and_destroy,
        )
        self._button_ok.pack()

    def mainloop(self):
        self._root.mainloop()

    def _apply_and_destroy(self):
        """
        Set values to parent and destroy this object
        """
        self._parent.advanced_options.architecture = self._architecture.get()
        self._parent.advanced_options.num_epochs = self._epochs.get()
        self._parent.advanced_options.delay = self._delay.get()
        self._root.destroy()

    def _set_architecture(self, val: _gui.Architecture):
        # val = _gui.Architecture.STANDARD  # TODO
        print(f"Set architecture as {val.value}")
        self._parent.advanced_options.architecture = val

    def _set_num_epochs(self):
        val = 100  # TODO
        print(f"Set num_epochs to {val}")
        self._parent.advanced_options.num_epochs = val

    def _set_delay(self):
        val = None  # TODO
        print(f"Set delay as to {val}")
        self._parent.advanced_options.delay = val


def _install_error():
    window = tk.Tk()
    label = tk.Label(window, width=45, height=2, text="The NAM training software has not been installed correctly.")
    label.pack()
    button = tk.Button(window, width=10, height=2, text="Quit", command=window.destroy)
    button.pack()
    window.mainloop()


def main():
    if _install_is_valid:
        gui = GUI()
        gui.mainloop()
    else:
        _install_error()


if __name__ == "__main__":
    main()
