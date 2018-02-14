import numpy as np

import tensorflow as tf

from tf_models.model import Model


class LFWNetwork(Model):
    def __init__(self, hyper_params_filepath):
        super(LFWNetwork, self).__init__(hyper_params_filepath)

    def _create_model(self, input_tensor, reuse_weights, is_deploy_model=False):
        outputs = {}
        with tf.variable_scope('NeuralNet') as scope:
            if reuse_weights:
                scope.reuse_variables()

            # TODO define net architecture.

            outputs["logits"] = input_tensor
        return outputs

    def _create_loss(self, labels, validation_labels=None):
        labels = tf.reshape(labels, [-1, self.hyper_params.arch.output_dimension])
        loss_op = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=self.model_train["logits"], labels=labels))
        train_op = tf.train.RMSPropOptimizer(learning_rate=self.hyper_params.train.learning_rate, decay=self.hyper_params.train.decay).minimize(loss_op)

        # Create a validation loss if possible.
        if validation_labels is not None:
            validation_labels = tf.reshape(validation_labels, [-1, self.hyper_params.arch.output_dimension])
            validation_loss_op = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=self.model_deploy["logits"], labels=validation_labels))

        return train_op
