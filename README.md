# starttf - Deeplearning Starterkit for Tensorflow [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This repo aims to contain everything required to quickly develop a deep neural network with tensorflow.
If I can find it the models will also contain pretrained weights.
The idea is that if you use existing dataset loaders and networks and only modify them, you will automatically obey best practices and have super fast training speeds.

## Writing your own models

See section 'Simple to use tensorflow' at the end of this document.


## Install

Properly install tensorflow-gpu please follow the [official instructions](https://www.tensorflow.org/install/) carefully.

Then, simply pip install from the github repo.

```bash
pip install https://github.com/penguinmenac3/starttf/archive/master.zip
```

### Optional Recommendations

For simple dataset access install opendatalake.

```bash
pip install https://github.com/penguinmenac3/opendatalake/archive/master.zip
```

## Running examples

You can launch your code from the command line like the example.

```bash
# Activate your virtual environment (in my case venv)
# Then do the following
(venv) $ pyhon -m starttf.examples.mnist.prepare_training
(venv) $ pyhon -m starttf.examples.mnist.train
```

## Datasets

For dataset support you can write your own generators or use opendatalake library including bindings to load many popular datasets in a unified format.
For details checkout the readme of opendatalake [**here**](https://github.com/penguinmenac3/opendatalake/blob/master/README.md).

## Models

There are some models implemented to tinker around with.
Most of the implementations are not done by me from scratch but rather refactoring of online found implementations.
Also the common models will come with pre trained weights I found on the internet.
Just check the comment at the top of their source files.

### Tensorflow Models

Every model returns a dictionary containing output tensors.

1. [Alexnet (single stream version)](starttf/models/alexnet.py)
2. [VGG 16](starttf/models/vgg16.py)
3. [VGG 16 pretrained](starttf/models/vgg16_encoder.py)
4. [GoogLeNet (Inception v3)](starttf/models/inception_v3.py)
5. [GoogLeNet Encoder (Inception v3)](starttf/models/inception_v3_encoder.py)
6. Overfeat/Tensorbox [TODO]
7. ResNet [TODO]
8. SegNet [TODO]
9. Mask RCNN [TODO]
10. monoDepth [TODO]
11. [TF Hub Wrapper](starttf/models/tf_hub_wrapper.py)

More non famous models by myself:

1. [CNN for MNIST (Digit Recognition)](starttf/models/mnist.py)
2. [GRU Function Classifier](starttf/models/gru_function_classifier.py)
3. CNN for LFW (Person Identification) [TODO]

### Tensorflow Examples

1. [MNIST](starttf/examples/mnist)
2. LFW [TODO]
3. Imagenet (Baselines) [TODO]
4. Bounding Box Regression [TODO]
5. Segmentations [TODO]
6. Instance Masks [TODO]
7. Reinforcement Learning [TODO]
8. [GRU Function Classifier](starttf/examples/gru_function_classifier)

## Simple to use tensorflow


### Simple Training (No Boilerplate)

There are pre-implemented models which can be glued together and trained with just a few lines.
However, before training you will have to create tf-records as shown in the section *Simple TF Record Creation*.
This is actually a full main file.

```python
# Import helpers
from starttf.estimators.scientific_estimator import easy_train_and_evaluate
from starttf.utils.hyperparams import load_params

# Import a/your model (here one for mnist)
from starttf.models.mnist import create_model

# Import your loss (here an example)
from starttf.examples.mnist.loss import create_loss

# Load params (here for mnist)
hyper_params = load_params("starttf/examples/mnist/hyper_params.json")

# Train model
easy_train_and_evaluate(hyper_params, mnist_model, create_loss)
```

### Quick Model Definition

Full sample [here](https://github.com/penguinmenac3/starttf/blob/master/starttf/models/mnist.py).

Simply implement a create_model function.
This model is only a feed forward model.

The model function returns a dictionary containing all layers that should be accessible from outside and a feed_dict prepopulated with e.g. hidden states for rnns.

```python
def create_model(input_tensor, mode, hyper_params):
    model = {}
    l2_weight = 0.0
    with tf.variable_scope('MnistNetwork') as scope:
        if mode == tf.estimator.ModeKeys.EVAL:
            scope.reuse_variables()

        # TODO Your model should go here
        model["logits"] = input_tensor
        model["probs"] = tf.nn.softmax(logits=model["logits"], name="probs")
    return model
```

### Quick Loss Definition

Full sample [here](https://github.com/penguinmenac3/starttf/blob/master/starttf/examples/mnist/loss.py).

```python
def create_loss(model, labels, mode, hyper_params):
    mode_name = mode_to_str(mode)
    metrics = {}

    # Add loss
    labels = tf.reshape(labels, [-1, 10])
    loss_op = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=model["logits"], labels=labels))
    tf.summary.scalar(mode_name + '/loss', loss_op)
    metrics[mode_name + '/loss'] = loss_op

    return loss_op, metrics
```

### Simple TF Record Creation

Full sample [here](https://github.com/penguinmenac3/starttf/blob/master/starttf/examples/mnist/prepare_training.py).

Fast training speed can be achieved by using tf records.
Actually the api only supports using tf records, to enforce usage for optimal performance.
However, usually tf records are a hastle to use the write_data method makes it simple.

```python
# Load the hyper parameters.
hyper_params = load_params("starttf/examples/mnist/hyper_params.json")

# Get a generator and its parameters
train_gen, train_gen_params = mnist(base_dir=hyper_params.problem.data_path, phase="train")
validation_gen, validation_gen_params = mnist(base_dir=hyper_params.problem.data_path, phase="validation")

# Create the paths where to write the records from the hyper parameter file.
train_record_path = os.path.join(hyper_params.train.tf_records_path, "train")
validation_record_path = os.path.join(hyper_params.train.tf_records_path, "validation")

# Write the data
write_data(hyper_params, train_record_path, train_gen, train_gen_params, 4)
write_data(hyper_params, validation_record_path, validation_gen, validation_gen_params, 2)
```

### Tensorboard Integration

Tensorboard integration is simple.
You just have to define a summary (e.g. a summary scalar for the loss) and it gets added to the tensorboard.
No worries when to summarize and how to call it and merging.
Simply define your summary and the rest is handled by the estimator.

### TF Estimator Support (Not Recommended)

Model and loss can be easily glued together in a model function and used with tf estimator.
`mode` is a `tf.estimator.ModeKeys` to be Estimator compatible.

```python
from starttf.models.mnist import create_model
from starttf.losses.mnist import create_loss

def my_model_fn(features, labels, mode, hyper_params):
    # Create a model
    model = create_model(features, mode, hyper_params)
    if tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.ModeKeys.EstimatorSpec(mode, predictions=model)
    
    # Add a loss
    loss, metrics = create_loss(model, labels, mode, hyper_params)
    if tf.estimators.ModeKeys.EVAL:
        return tf.estimator.ModeKeys.EstimatorSpec(mode, loss=loss, eval_metric_ops=metrics)

    # Define a training operation
    if mode == tf.estimator.ModeKeys.TRAIN:
        train_op = tf.train.RMSPropOptimizer(learning_rate=hyper_params.train.learning_rate,
                                     decay=hyper_params.train.decay).minimize(loss)
    
        return tf.estimator.EstimatorSpec(mode, loss=loss, train_op=train_op)

    raise RuntimeError("Unexpected mode.")
```

### More details

More details can be found in starttf/examples or starttf/models. Mnist is a simple example for starters.
