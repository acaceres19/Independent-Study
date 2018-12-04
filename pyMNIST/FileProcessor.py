import os
import imageio
import time
import numpy as np
from utils import mnist_reader
import FeedforwardNeuralNet
import ProgressBar


# Data Processing
def process_mnist_data(dataset_name):
    """
    Process a dataset with the format used by MNIST, present in the 'data' folder.
    :param dataset_name: name of the folder within the 'data' folder to get the files from
    :return: a tuple with two zipped lists, the training input/outputs and the testing input/outputs
    """
    def process_mnist_input(input_list):
        """
        Process a list of inputs, where one input is a list of integers corresponding to the pixels of the images, by
        dividing each input by 256 to limit the inputs to values between 0 and 1.
        :param input_list: a list of lists of integers, where each list is one input.
        :return: a list of numpy column arrays with length 784, with floats between 0 and 1.
        """
        # Progress Bar
        start_time = time.time()
        print("Processing Input")
        ProgressBar.draw_bar(0, 30, 0)
        inputs_completed = 0

        processed_inputs = []
        for old_input in input_list:
            new_input = []
            for integer in old_input:
                new_input.append([integer / 256.0])
            processed_inputs.append(np.array(new_input))

            inputs_completed += 1.0
            ProgressBar.draw_bar(inputs_completed / len(input_list), 30, time.time() - start_time)
        print("Input processing took " + ProgressBar.time_to_string(time.time() - start_time) + ".")
        return processed_inputs

    def process_mnist_output(output_list):
        """
        Process a list of outputs, where one output is an integer
        corresponding to the group that the input should be classified under.
        :param output_list: a list of integers, where each integer is one output.
        :return: a list of numpy arrays with length 10, with 0 at all indices except the integer from data_list
        """
        start_time = time.time()
        print("Processing Output")
        ProgressBar.draw_bar(0, 30, 0)
        outputs_completed = 0

        processed_outputs = []
        for old_output in output_list:
            new_output = []
            for i in range(10):
                if i == old_output:
                    new_output.append([1])
                else:
                    new_output.append([0])
            processed_outputs.append(np.array(new_output))

            outputs_completed += 1.0
            ProgressBar.draw_bar(outputs_completed / len(output_list), 30, time.time() - start_time)
        print("Output processing took " + ProgressBar.time_to_string(time.time() - start_time) + ".")
        return processed_outputs

    data = "data/" + dataset_name
    x_train, y_train = mnist_reader.load_mnist(data, kind='train')
    x_test, y_test = mnist_reader.load_mnist(data, kind='t10k')

    train_io = list(zip(process_mnist_input(x_train), process_mnist_output(y_train)))
    test_io = list(zip(process_mnist_input(x_test), process_mnist_output(y_test)))
    return train_io, test_io


def user_drawings_to_inputs(path, base_title):
    """
    From a folder of user drawings, convert them into a format that can be processed by a neural network.
    :param path: the folder to get the user drawings from
    :param base_title: file name without the added number or the file extension (ignores files without this name)
    :return: list of tuples with an input and its corresponding file name
    """
    input_list = []
    file_names = []
    for file_name in os.listdir(os.getcwd() + "/" + path):
        if file_name[:len(base_title)] == base_title:
            input_list.append(imageio.imread(path + "/" + file_name, as_gray=True))
            file_names.append(file_name)
    processed_input_list = []
    for old_input in input_list:
        new_input = []
        for row in old_input:
            for element in row:
                new_input.append([(255 - element) / 256])
        processed_input_list.append(np.array(new_input))
    return zip(processed_input_list, file_names)


def draw_input_to_ascii(input_list):
    """
    Prints an input to the network in ASCII characters.
    :param input_list: a list of floats between 0 and 1, representing an input to the neural network.
    """
    i = 0
    for r in range(28):
        for c in range(28):
            char = ('.', '#')[input_list[r * 28 + c][0] != 0]
            print(char, end='')
            i += 1
        print("")
    print("")


# Handling Neural Network Information Files
def write_net_file(net, dataset_name, num_trials, num_epochs, batch_size, num_correct_list):
    """
    Create a file containing all the information about a neural net after training.
    :param net: the trained neural network
    :param dataset_name: name of the dataset that the network was trained with
    :param num_trials: the number of trials the network was trained with
    :param num_epochs: the number of epochs the network was trained with
    :param batch_size: the batch size the network was trained with
    :param num_correct_list: the list of numbers of correct classifications after each training trial
    :return: the file name that the net file was written under.
    """
    file_name = get_complete_title(dataset_name + " Trial", "weight_database", ".txt")
    with open(file_name, 'w') as file:
        file.write("Dataset: " + dataset_name + "\n\n")
        file.write("Network Size: ")
        for num in net.size:
            file.write(str(num) + " ")
        file.write("\nLearning Rate: " + str(net.learning_rate) + "\n"
                   "Number of Epochs: " + str(num_epochs) + "\n" +
                   "Batch Size: " + str(batch_size) + "\n\n")
        for i in range(num_trials):
            file.write("Trial " + str(i) + ": " + str(num_correct_list[i]) + " Correct\n")

        file.write("\nWeight Matrices\n")
        for i in range(len(net.weight_matrices)):
            file.write("-Weight Matrix " + str(i) + "\n")
            for row in net.weight_matrices[i]:
                for element in row:
                    file.write(str(element) + " ")
                file.write("\n")
            file.write("\n")

        file.write("\n\nBias Matrices\n")
        for i in range(len(net.bias_matrices)):
            file.write("-Bias Matrix " + str(i) + "\n")
            for col in net.bias_matrices[i]:
                file.write(str(col[0]) + " ")
            file.write("\n\n")
    return file_name


def read_net_file(file_name):
    """
    Creates a NeuralNet object with preloaded weights and biases from a file.
    :param file_name: the path and file name to be used to preload the weights and biases
    :return: a neural net with weights and biases from the file.
    """
    new_weights = []
    new_biases = []
    with open(file_name, 'r') as file:
        file.readlines(2)
        str_list = file.readline().split()
        size = []
        for string in str_list[2:]:
            size.append(int(string))
        net = FeedforwardNeuralNet.NeuralNet(size)
        file.readlines(12)
        for i in range(len(net.weight_matrices)):
            weight_matrix = []
            for j in range(len(net.weight_matrices[i])):
                line_data = file.readline().split()
                weight_row = []
                for string in line_data:
                    weight_row.append(float(string))
                weight_matrix.append(weight_row)
            new_weights.append(np.array(weight_matrix))
            file.readlines(2)
        file.readlines(3)
        for i in range(len(net.bias_matrices)):
            bias_matrix = []
            line_data = file.readline().split()
            for string in line_data:
                bias_matrix.append([float(string)])
            new_biases.append(np.array(bias_matrix))
            file.readlines(2)
    net.weight_matrices = new_weights
    net.bias_matrices = new_biases
    return net


# Miscellaneous
def get_complete_title(base, path, file_type):
    """
    Given a folder and a file name, add numbers to ensure the new file will not overwrite any existing files.
    :param base: file name without the file extension
    :param path: path to the folder to store the file in question, excluding the first and last '/'
    :param file_type: file extension given to the file you are trying to name
    :return: string with a path and file name that doesn't match any existing files in that path
    """
    title = base + " "
    counter = 0
    unique = False
    while not unique:
        title = base + " " + str(counter)
        unique = True
        for item in os.listdir(os.getcwd() + "/" + path):
            if item == title + file_type:
                unique = False
        counter += 1
    complete_title = path + "/" + title + file_type
    return complete_title


# Data Augmentation
def bound_box_of_values(input_list):
    """
    :param input_list: a one-dimensional numpy column array containing values for a handwritten digit.
    Calculates the box of values surrounding the image in question.
    :return: ((min_x, min_y), (max_x, max_y))
    """
    minimum, maximum = [28, 28], [-1, -1]
    for r in range(28):
        for c in range(28):
            v = input_list[r * 28 + c][0]
            if v != 0:
                if c < minimum[0]:
                    minimum[0] = c
                if r < minimum[1]:
                    minimum[1] = r
                if c > maximum[0]:
                    maximum[0] = c
                if r > maximum[1]:
                    maximum[1] = r
    return (minimum[0], minimum[1]), (maximum[0], maximum[1])


def calculate_shift_ranges(input_list):
    """
    :param input_list: a one-dimensional numpy column array containing values for a handwritten digit.
    Calculates the maximum range by which to shift the image to reach the boundary
    :return: ((max_left, max_right),(max_up, max_down))
    """
    bounds = bound_box_of_values(input_list)
    x_range = (-bounds[0][0], 28 - bounds[1][0] - 1)
    y_range = (-bounds[0][1], 28 - bounds[1][1] - 1)
    return x_range, y_range


def range_of_shiftable_positions(input_list):
    """
    :param input_list: a one-dimensional numpy column array containing values for a handwritten digit.
    :return: a sequence of shift deltas to get every possible position of the input list within the bounds of the image.
        Note that the sequence assumes that the image is moving.
    """
    bounds = bound_box_of_values(input_list)
    result = []
    dx, dy = bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1]
    result.append((-bounds[0][0], -bounds[0][1]))
    for r in range(28 - dy):
        if dx > 0:
            for c in range(28 - dx - 1):
                result.append((+1, 0))
        if r < 28 - dy - 1:
            result.append((-(28 - dx - 1), +1))
    return result


def shift_all_values(input_list, xy_delta):
    """
    return a new list of inputs that is the original inputs shifted by the delta.
    :param input_list: a one-dimensional numpy column array containing values for a handwritten digit.
    :param xy_delta: a shift delta that produces a new position for the image in the input_list
    :return:
    """
    # create a 2D array version of the 1D array
    two_dim_copy = []
    new_input_list = []
    for r in range(28):
        two_dim_copy.append([])
        for c in range(28):
            two_dim_copy[r].append(input_list[r * 28 + c][0])
    for r in range(len(two_dim_copy)):
        shift_list(two_dim_copy[r], xy_delta[0], 0)
    shift_list(two_dim_copy, xy_delta[1], [0] * len(two_dim_copy[0]))
    # copy it back now
    for r in range(28):
        for c in range(28):
            new_input_list[r * 28 + c][0] = two_dim_copy[r][c]
    return new_input_list


def shift_list(values, delta, fill_extra_with=None):
    """
    Shift a list of inputs in-place a certain change delta.
    :param values: the inputs to shift.
    :param delta: the change with which to shift the inputs.
    :param fill_extra_with: the value to fill the empty spaces with
    :return: None
    """
    import copy
    if delta < 0:  # go backwards, losing values at the front
        for i in range(0, len(values) + delta):
            values[i] = values[i - delta]
        if fill_extra_with is not None:
            for i in range(len(values) + delta, len(values)):
                values[i] = copy.copy(fill_extra_with)
    if delta > 0:
        for i in range(len(values) - 1, -1, -1):
            values[i] = values[i - delta]
        if fill_extra_with is not None:
            for i in range(delta - 1, -1, -1):
                values[i] = copy.copy(fill_extra_with)
