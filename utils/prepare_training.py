import os
from multiprocessing import Pool
import tensorflow as tf
from os import listdir
from os.path import isfile, join


def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _write_tf_record_pool_helper(args):
    data, num_threads, i, record_filename, preprocess_feature, preprocess_label = args
    _write_tf_record(data(num_threads, i), record_filename, preprocess_feature, preprocess_label)


def _write_tf_record(data, record_filename, preprocess_feature=None, preprocess_label=None):
    writer = tf.python_io.TFRecordWriter(record_filename)

    for feature, label in data:
        if preprocess_feature is not None:
            feature = preprocess_feature(feature)
        if preprocess_label is not None:
            label = preprocess_label(label)

        example = tf.train.Example(features=tf.train.Features(
            feature={
                'feature': _bytes_feature(feature.tobytes()),
                'label': _bytes_feature(label.tobytes())
                }))
        writer.write(example.SerializeToString())
    writer.close()


def _read_tf_record(record_filename, feature_shape, label_shape, feature_type, label_type):
    reader = tf.TFRecordReader()
    _, serialized_example = reader.read(record_filename)

    data = tf.parse_single_example(
        serialized_example,
        features={
            'feature': tf.FixedLenFeature([], tf.string),
            'label':   tf.FixedLenFeature([], tf.string)
        })

    feature = tf.decode_raw(data['feature'], feature_type)
    feature.set_shape(feature_shape)
    label = tf.decode_raw(data['label'], label_type)
    label.set_shape(label_shape)

    return feature, label


def read_tf_records(folder, phase, batch_size, feature_shape, label_shape, feature_type, label_type, num_threads=4):
    filenames = [folder + "/" + f for f in listdir(folder) if isfile(join(folder, f)) and phase in f]

    # Create a tf object for the filename list and the readers.
    filename_queue = tf.train.string_input_producer(filenames, num_epochs=50000)
    readers = [_read_tf_record(filename_queue, feature_shape, label_shape, feature_type, label_type) for _ in range(num_threads)]

    feature_batch, label_batch = tf.train.shuffle_batch_join(
        readers,
        batch_size=batch_size,
        capacity=10 * batch_size,
        min_after_dequeue=5 * batch_size
    )

    return feature_batch, label_batch


def write_tf_records(output_folder, num_threads_train, num_threads_validation, train_data, validation_data, preprocess_feature=None, preprocess_label=None):
    args_train = [(train_data, num_threads_train, i, os.path.join(output_folder, "train_%d.tfrecords" % i ), preprocess_feature, preprocess_label) for i in range(num_threads_train)]
    args_validation = [(validation_data, num_threads_validation, i, os.path.join(output_folder, "validation_%d.tfrecords" % i ), preprocess_feature, preprocess_label) for i in range(num_threads_validation)]

    for arg in args_train + args_validation:
        _write_tf_record_pool_helper(arg)
    
    #pool = Pool(processes=(num_threads_train + num_threads_validation))
    #pool.map(_write_tf_record_pool_helper, args_train + args_validation)