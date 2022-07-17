# NAM: neural amp modeler

This is the training part of NAM.
For the code to create the plugin with a trained model, see my
[iPlug2 fork](https://github.com/sdatkinson/iPlug2).

This repository handles training, reamping, and exporting the weights of a model (to
use with [the iPlug2 plugin]())

## How to use (Google Colab)

If you don't have a good computer for training ML models, you can run the
notebook located at `bin/train/colab.ipynb` in the cloud using Google Colab--no
local installation required!

Go to [colab.research.google.com](https://colab.research.google.com), open the
notebook using the "GitHub" tab, and go!

## How to use (Local)

Alternatively, the you can clone this repo and use it in the following ways on
your own computer:

### Train a model

You'll need at least two mono wav files: the input (DI) and the amped sound (without the cab).
You can either record enough to have a training and validation set in the same file and
split the file, or you can use 4 files (input/output for train/test).
Also, you can provide _multiple_ file pairs for training (or validation).

For the first option, Modify `bin/train/inputs/config_data_single_pair.json` to point at the audio files, and set the
start/stop to the point (in samples) where the training segment ends and the validation
starts.
For the second option, modify and use `bin/train/inputs/config_data_two_pairs.json`.

Then run:

```bash
python bin/train/main.py \
bin/train/inputs/config_data.json \
bin/train/inputs/config_model.json \
bin/train/inputs/config_learning.json \
bin/train/outputs/MyAmp
```

### Run a model on an input signal ("reamping")

Handy if you want to just check it out without going through the trouble of building the
plugin.

For example:

```bash
python bin/run.py \
path/to/source.wav \
path/to/config_model.json \
path/to/checkpoints/epoch=123_val_loss=0.000010.ckpt \
path/to/output.wav
```

### Export a model (to use with [the plugin](https://github.com/sdatkinson/iPlug2))

Let's get ready to rock!

```bash
python bin/export.py \
path/to/config_model.json \
path/to/checkpoints/epoch=123_val_loss=0.000010.ckpt \
path/to/exported_models/MyAmp
```

You'll want the `HardCodedModel.h` to paste over into the plugin source (i.e. [here](https://github.com/sdatkinson/iPlug2/blob/5a0f533f7a9e4ee691da26adb2a38d87905e87fe/Examples/NAM/HardCodedModel.h)).

## Advanced usage

The model architecture in `config_model.json` should work plenty good. However, if you
want to, you can increase the number of channels and the model will generally fit
better (though it'll get closer to the threshold of real-time. 20 works for a "large"
model and is still about 6x real time on my desktop).

If you want to mess with the model architecture and end up with a different receptive
field (e.g. by messing with the dilation pattern), then you need to make sure that `nx`
is changed accordingly in the data setup.
The default architecture has a receptive field of 8191 samples, so `nx` is `8191`.
Generally, for the conv net architecture the receptive field is one elss than the sum of the `dilations`.

You can train for shorter or longer.
1000 gives pretty great results, but if you're impatient you can sometimes get away with
comparable results after 500 epochs, and you might nto even be able to tell the
difference with far fewer (maybe 200?...100?)
